#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include "interpreter.h"
#include "crypto_len.h"
#include "program.h"
#include "utils.h"
#include "sparkle/esch/esch.h"
#include "SEalgo.h"

// global pointer to bytecode file
static u8* bcptr;

static u32 load_bytes(u32 bytelen)
// big-endian
{
  u32 n;
  switch (bytelen){
    case 1:
      n = bcptr[0];
      break;
    case 2:
      n = (bcptr[0] << 8)
        | (bcptr[1]     );
      break;
    case 3:
      n = (bcptr[0] << 16)
        | (bcptr[1] <<  8)
        | (bcptr[2]      );
      break;
    case 4:
      n = (bcptr[0] << 24)
        | (bcptr[1] << 16)
        | (bcptr[2] <<  8)
        | (bcptr[3]      );
      break;
    default:
      fprintf(stderr, "Invalid number of bytes (%d).\n", bytelen);
      exit(EXIT_FAILURE);
    }
  bcptr += bytelen;
  return n;
}

static void interpret_meta(u32 *memory_count)
{
  u32 version, word_size, lin_bc, lout_bc, r_bc, s_bc;
  // version (32)
  version = load_bytes(4);
  if (version != VERSION){
    fprintf(stderr, "Invalid version (%d). Require %d\n", version, VERSION);
    exit(EXIT_FAILURE);
  }
  // word_size (32)
  word_size = load_bytes(4);
  if (word_size != WORD_SIZE){
    fprintf(stderr, "Invalid word_size (%d). Require %d\n", \
                     word_size, WORD_SIZE);
    exit(EXIT_FAILURE);
  }
  // LLMI_max_input_count (l_in) (32)
  lin_bc = load_bytes(4);
  if (lin_bc != LLMI_MAX_INPUT_COUNT){
    fprintf(stderr, "Invalid LLMI_max_input_count (%d). Require %d\n", \
                     lin_bc, LLMI_MAX_INPUT_COUNT);
    exit(EXIT_FAILURE);
  }
  // LLMI_max_output_count (l_out) (32)
  lout_bc = load_bytes(4);
  if (lout_bc != LLMI_MAX_OUTPUT_COUNT){
    fprintf(stderr, "Invalid LLMI_max_output_count (%d). Require %d\n", \
                     lout_bc, LLMI_MAX_OUTPUT_COUNT);
    exit(EXIT_FAILURE);
  }
  // register_count (r) (32)
  r_bc = load_bytes(4);
  if (r_bc != REGISTER_COUNT){
    fprintf(stderr, "Invalid register_count (%d). Require %d\n", \
                     r_bc, REGISTER_COUNT);
    exit(EXIT_FAILURE);
  }
  // LLS_max_length (s) (32)
  s_bc = load_bytes(4);
  if (s_bc != LLS_MAX_LENGTH){
    fprintf(stderr, "Invalid LLS_max_length (%d). Require %d\n", \
                     s_bc, LLS_MAX_LENGTH);
    exit(EXIT_FAILURE);
  }
  // memory_count (32)
  *memory_count = load_bytes(4);
}

static void interpret_prog(Program *program,
                               u32 lb_m,
                               u32 lb_o)
{
  u32 i, j;
  // input_count (lb_m)
  program->inp_count = load_bytes(lb_m);
  program->mem_inps = malloc(program->inp_count * sizeof(u32));
  for(i=0; i<program->inp_count; i++) program->mem_inps[i] = load_bytes(lb_m);
  // output_count (lb_m)
  program->out_count = load_bytes(lb_m);
  program->mem_outs = malloc(program->out_count * sizeof(u32));
  for(i=0; i<program->out_count; i++) program->mem_outs[i] = load_bytes(lb_m);
  // LLMI_count (32)
  program->llmi_count = load_bytes(4);
  program->llmis = malloc(program->llmi_count * sizeof(LLMI));
  for(i=0; i<program->llmi_count; i++){
    LLMI  *llmi  = &(program->llmis[i]);
    AELLS *aells = &(llmi->aells);

    // LLMI inputs
    llmi->inp_count = load_bytes(lb_m);
    aells->inp_count = llmi->inp_count;
    llmi->mem_inps = malloc(llmi->inp_count * sizeof(u32));
    for(j=0; j<llmi->inp_count; j++) llmi->mem_inps[j] = load_bytes(lb_m);

    // LLMI outputs
    llmi->out_count = load_bytes(lb_m);
    aells->out_count = llmi->out_count;
    llmi->mem_outs = malloc(llmi->out_count * sizeof(u32));
    for(j=0; j<llmi->out_count; j++) llmi->mem_outs[j] = load_bytes(lb_m);

    // instrID
    aells->instrID = load_bytes(4);
    aells->reveal_flag = load_bytes(1);

    // inputIDs
    aells->inputIDs = malloc(aells->inp_count * sizeof(ID));
    for(j=0; j < aells->inp_count; j++){
      aells->inputIDs[j].instrID = load_bytes(4);
      aells->inputIDs[j].outputID = load_bytes(lb_o);
    }

    // LLS_bytelen
    aells->bytelen = load_bytes(4);
    aells->bytecode = bcptr;
    bcptr += aells->bytelen;
  }
}

void interpret(u8  *bytecode, unsigned long bytecode_len,
               uSE *prog_inps, u32 prog_inpcount,
               uSE *prog_outs, u32 prog_outcount)
{
  bcptr = bytecode;

  u32 memory_count;
  interpret_meta(&memory_count);

  u32 r = REGISTER_COUNT;

  // lb_c: bytelen for memory cell
  u32 lb_m = ((u32) ceilf(log2f(memory_count)) + 7) / 8;
  // lb_c: bytelen for a constant
  u32 lb_c = WORD_SIZE / 8;
  // lb_r: bytelen for 1 register
  u32 lb_r = ((u32) ceilf(log2f(r)) + 7) / 8;
  // lb_o: bytelen for an outputID
  u32 lb_o = ((u32) ceilf(log2f(l_out)) + 7) / 8;

  // header (ciphertext of shared key + number of inputs)
  u8* header = bcptr; bcptr += CT_SEPUB_INBYTES;

  // program
  Program program;
  interpret_prog(&program, lb_m, lb_o);
  if (bcptr != bytecode + bytecode_len){
    fprintf(stderr, "Interpret failed: error while reading bytecode.\n");
    exit(EXIT_FAILURE);
  }

  // check program input_cout and output_count
  if (prog_inpcount != program.inp_count){
    fprintf(stderr, "Invalid program input_count! Provided %u. Bytecode required %u\n",
                      prog_inpcount, program.inp_count);
    exit(EXIT_FAILURE);
  }
  if (prog_outcount != program.out_count){
    fprintf(stderr, "Invalid program output_count! Provided %u. Bytecode required %u\n",
                      prog_outcount, program.out_count);
    exit(EXIT_FAILURE);
  }

  u32 i, j, k;
  // Step 1: batching and compute H
  u32 L = (program.inp_count + l_out - 1) / l_out;
  uSE **X = malloc((L+1) * sizeof(uSE *));
  for(i=1; i<= L; i++){ // Ignore X[0] for indice compatible with H
    X[i] = malloc(l_out * sizeof(uSE));
    for(j=0; j<l_out; j++){
      k = (i-1)*l_out + j;
      X[i][j] = (k < program.inp_count) ? prog_inps[k] : 0;
    }
  }

  u8 **H = malloc((L+1) * sizeof(u8 *));
  H[0] = malloc(HASH_INBYTES * sizeof(u8));
  for(j=0; j<HASH_INBYTES; j++) H[0][j] = 0;
  for(i=1; i<=L; i++){
    H[i] = malloc(HASH_INBYTES * sizeof(u8));
    hashchain(H[i], H[i-1], X[i]);
  }

  // Step 2: SE("Start", header, H_L)
  u8 **Cin = malloc((L+1) * sizeof(u8 *));
  for(i=0; i<=L; i++) Cin[i] = malloc(CIN_INBYTES * sizeof(u8));
  u8 execID[HASH_INBYTES];
  u8 esharedkey[ENCRYPTED_SHAREDKEY_INBYTES];
  SEstart(esharedkey, execID, Cin[L], header, lb_m, H[L]);

  // Step 3: SE("Input", E_ID, i, H_{i-1}, X_i, C_i^in)
  EWORD *C = malloc((l_out*L) * sizeof(EWORD));
  for(i=L; i>0; i--){
    SEinput(Cin[i-1], C+(i-1)*l_out,
            execID, i, H[i-1], X[i], Cin[i]);
  }

  // Store encrypted intput words into memory
  EWORD *memory = malloc(memory_count * sizeof(EWORD));
  for(i=0; i<program.inp_count; i++) memory[program.mem_inps[i]] = C[i];

  // Step 4: SE("Eval", E_ID, E_K, MI_\nu, C_1^*, ..., C_l^*)
  for(i=0; i<program.llmi_count; i++){
    LLMI *llmi = &program.llmis[i];
    EWORD *inps = malloc(llmi->inp_count * sizeof(EWORD));
    EWORD *outs = malloc(llmi->out_count * sizeof(EWORD));
    // Load encrypted input words from memory
    for(j=0; j<llmi->inp_count; j++) inps[j] = memory[llmi->mem_inps[j]];
    // Request SE to execute
    SEeval(outs, execID, esharedkey, &llmi->aells, inps, r, lb_m, lb_r, lb_c, lb_o);
    // Store encrypted output words into memory
    for(j=0; j<llmi->out_count; j++) memory[llmi->mem_outs[j]] = outs[j];

    free(inps);
    free(outs);
  }

  for(i=0; i<program.out_count; i++)
    prog_outs[i] = load_word(memory[program.mem_outs[i]].eword, WORD_INBYTES);

  // free memory
  free(memory);
  free(C);
  for(i=0; i<=L; i++) free(Cin[i]); free(Cin);
  for(i=0; i<=L; i++) free(H[i]); free(H);
  for(i=1; i<=L; i++) free(X[i]); free(X);
  free(program.mem_inps);
  free(program.mem_outs);
  for(i=0; i<program.llmi_count; i++) free(program.llmis[i].mem_inps);
  for(i=0; i<program.llmi_count; i++) free(program.llmis[i].mem_outs);
  for(i=0; i<program.llmi_count; i++) free(program.llmis[i].aells.inputIDs);
}