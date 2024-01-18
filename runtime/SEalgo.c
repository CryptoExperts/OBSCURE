#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sodium.h>
#include "SEconfig.h"
#include "SEalgo.h"
#include "utils.h"
#include "sparkle/esch/esch.h"
#include "sparkle/schwaemm/schwaemm.h"
#include "opcode.h"

/******************************************************************************
 *                        hard-coded keys
 ******************************************************************************/
// pub_SE
static u8 pubkey[32] = {0xC4, 0x82, 0x46, 0x24, 0x5F, 0x2E, 0x8D, 0x45, \
                        0x6F, 0x14, 0x1D, 0x07, 0x4A, 0x3A, 0x97, 0x12, \
                        0x59, 0x0D, 0x54, 0xA4, 0x44, 0x04, 0x9C, 0xE9, \
                        0xBA, 0xCB, 0x59, 0xD0, 0xDD, 0xC4, 0x76, 0x62 };
// priv_SE
static u8 prvkey[32] = {0x2D, 0xC8, 0x72, 0x0F, 0xD4, 0x96, 0x4E, 0x38, \
                        0x74, 0x92, 0x22, 0xAA, 0xF5, 0x00, 0x6B, 0xC8, \
                        0xAF, 0x6D, 0x4C, 0xC6, 0x78, 0x85, 0xB0, 0x08, \
                        0x31, 0x83, 0x80, 0xC9, 0xC0, 0x14, 0x79, 0xB0 };
// K_SE
static u8 seckey[16] = {0x2, 0x2, 0x2, 0x2, 0x2, 0x2, 0x2, 0x2,
                        0x2, 0x2, 0x2, 0x2, 0x2, 0x2, 0x2, 0x2};

static u8 *ptr;
/******************************************************************************
 *                        functions
 ******************************************************************************/
static void hash_withprefix(u8 h[HASH_INBYTES], u32 prefix, u8* msg, u64 mlen)
{
  u8 msghash[4+mlen];
  u32_tobytes(msghash, 4, prefix);
  memcpy(msghash+4, msg, mlen);
  crypto_hash(h, msghash, mlen+4);
}

static void LLS_decrypt(u8 *lls_bytecode, AELLS *aells, u8 *shared_key, u32 lb_m, u32 lb_o)
{
  u32 i;
  u8 nonce[NONCE_INBYTES];
  for(i=0; i<HASH_INBYTES; i++) nonce[i] = 0;
  u8 instrID_bstr[U32_INBYTES];
  u32_tobytes(instrID_bstr, U32_INBYTES, aells->instrID);
  memcpy(nonce+NONCE_INBYTES-U32_INBYTES, instrID_bstr, U32_INBYTES);

  u64 adlen = U32_INBYTES + FLAG_INBYTES + lb_m*2 + (U32_INBYTES + lb_o)*aells->inp_count;
  u8 *ad = malloc(adlen);
  memcpy(ad, instrID_bstr, U32_INBYTES);
  u32_tobytes(ad+U32_INBYTES, FLAG_INBYTES, aells->reveal_flag);
  u32_tobytes(ad+U32_INBYTES+FLAG_INBYTES, lb_m, aells->inp_count);
  u8 *_ptr = ad + U32_INBYTES + FLAG_INBYTES + lb_m;
  for(i=0; i<aells->inp_count; i++){
    u32_tobytes(_ptr, U32_INBYTES, aells->inputIDs[i].instrID); _ptr += U32_INBYTES;
    u32_tobytes(_ptr, lb_o, aells->inputIDs[i].outputID); _ptr += lb_o;
  }
  u32_tobytes(_ptr, lb_m, aells->out_count); _ptr += lb_m;

  u64 mlen;
  int ret = crypto_aead_decrypt(lls_bytecode, &mlen,
                                NULL,
                                aells->bytecode, aells->bytelen,
                                ad, adlen,
                                nonce, shared_key);
  if (ret != 0 || mlen != aells->bytelen-MAC_INBYTES){
    fprintf(stderr, "Authenticated decryption LLS failed!\n");
    exit(EXIT_FAILURE);
  }

  free(ad);
}

static void EWORD_decrypt(uSE *reg, AELLS *aells, u8 *execID, EWORD *Cx)
{
  u8 bword[WORD_INBYTES];
  uSE word;
  u32 i;
  u64 mlen;
  int ret;
  u8 ad[A_INBYTES];
  u8 nonce[NONCE_INBYTES];
  memcpy(ad+2*U32_INBYTES, execID, HASH_INBYTES);
  for(i=0; i<aells->inp_count; i++){
    u32_tobytes(ad, U32_INBYTES, aells->inputIDs[i].instrID);
    u32_tobytes(ad+U32_INBYTES, U32_INBYTES, aells->inputIDs[i].outputID);
    hash_withprefix(nonce, 3, ad, A_INBYTES);
    ret = crypto_aead_decrypt(bword, &mlen,
                              NULL,
                              Cx[i].eword, C_INBYTES,
                              ad, A_INBYTES,
                              nonce, seckey);
    if (ret != 0 || mlen != WORD_INBYTES){
      fprintf(stderr, "SEeval: Authenticated decrypting encrypted word failed. (LLMI,instrID,outputID) = (%u,%u,%u)\n",
                      aells->instrID, aells->inputIDs[i].instrID, aells->inputIDs[i].outputID);
      exit(EXIT_FAILURE);
    }

    word = load_word(bword, WORD_INBYTES);
    reg[i] = word;
  }
}

static void EWORD_encrypt(EWORD *Cr, AELLS *aells, u8 *execID, uSE *reg, u32 r)
{
  u32 i;
  u64 clen;
  u8 bword[WORD_INBYTES];
  u8 ad[A_INBYTES];
  u8 nonce[NONCE_INBYTES];
  u32_tobytes(ad, U32_INBYTES, aells->instrID);
  memcpy(ad+2*U32_INBYTES, execID, HASH_INBYTES);
  for(i=0; i<aells->out_count; i++){
    word_tobytes(bword, reg[r-l_out+i]);
    u32_tobytes(ad+U32_INBYTES, U32_INBYTES, i);
    hash_withprefix(nonce, 3, ad, A_INBYTES);
    crypto_aead_encrypt(Cr[i].eword, &clen,
                        bword, WORD_INBYTES,
                        ad, A_INBYTES,
                        NULL,
                        nonce, seckey);
    if (clen != C_INBYTES){
      fprintf(stderr, "SEeval: Encrypting word (C) failed.\n");
      exit(EXIT_FAILURE);
    }
  }
}

static void EWORD_encode(EWORD *Cr, AELLS *aells, uSE *reg, u32 r)
{
  u32 i;
  u8 bword[WORD_INBYTES];
  for(i=0; i<aells->out_count; i++){
    word_tobytes(bword, reg[r-l_out+i]);
    memcpy(Cr[i].eword, bword, WORD_INBYTES);
  }
}

static void instruction_execute(uSE *ret, u8 opcode,
                                uSE operand1,
                                uSE operand2,
                                uSE operand3){
  uSE result;
  switch (opcode){
    case MOV:
      result = operand1; // omit operand 2
      break;
    case XOR:
      result = operand1 ^ operand2;
      break;
    case OR:
      result = operand1 | operand2;
      break;
    case AND:
      result = operand1 & operand2;
      break;
    case LSL:
      result = operand1 << operand2;
      break;
    case LSR:
      result = operand1 >> operand2;
      break;
    case LT:
      result = operand1 < operand2;
      break;
    case ADD:
      result = operand1 + operand2;
      break;
    case SUB:
      result = operand1 - operand2;
      break;
    case MUL:
      result = operand1 * operand2;
      break;
    case EQ:
      result = operand1 == operand2;
      break;
    case DIV:
      result = operand1 / operand2;
      break;
    case MOD:
      result = operand1 % operand2;
      break;
    case CMOV:
      result = operand1 ? operand2 : operand3;
      break;
    default:
        fprintf(stderr, "Invalid opcode: %d.\n", opcode);
        exit(EXIT_FAILURE);
  }
  *ret = result;
}

static uSE load_regvalue(u32 bytelen, uSE *reg){
  u32 src = load_u32(ptr, bytelen);
  uSE val = reg[src];
  ptr += bytelen;
  return val;
}

static uSE load_immvalue(u32 bytelen){
  uSE val = load_word(ptr, bytelen);
  ptr += bytelen;
  return val;
}

static void LLS_execute(uSE *reg,
                        u8 *lls_bytecode,
                        u32 lls_bytelen,
                        u32 lb_c,
                        u32 lb_r)
{
  ptr = lls_bytecode;
  u32 counter = 0;
  while (ptr != lls_bytecode + lls_bytelen){
    counter++;
    if (counter > LLS_MAX_LENGTH){
      fprintf(stderr, "Execute LLS failed: counter=%d > %d=LLS_MAX_LENGTH.\n",
              counter, LLS_MAX_LENGTH);
      exit(EXIT_FAILURE);
    }

    u8 opcode   = (*ptr & 0xF0) >> 4; // first 4 bits
    u8 flag     = (*ptr & 0x0F);      // last 4 bits
    ptr++;
    if (opcode == NOP) continue;

    u32 dst;
    uSE ret, val1, val2 = 0, val3 = 0;

    dst = load_u32(ptr, lb_r); ptr += lb_r;

    switch (flag){
      case INN:
        val1 = load_immvalue(lb_c);
        break;
      case IRN:
        val1 = load_immvalue(lb_c);
        val2 = load_regvalue(lb_r, reg);
        break;
      case IRR:
        val1 = load_immvalue(lb_c);
        val2 = load_regvalue(lb_r, reg);
        val3 = load_regvalue(lb_r, reg);
        break;
      case IRI:
        val1 = load_immvalue(lb_c);
        val2 = load_regvalue(lb_r, reg);
        val3 = load_immvalue(lb_c);
        break;
      case IIN:
        val1 = load_immvalue(lb_c);
        val2 = load_immvalue(lb_c);
        break;
      case IIR:
        val1 = load_immvalue(lb_c);
        val2 = load_immvalue(lb_c);
        val3 = load_regvalue(lb_r, reg);
        break;
      case III:
        val1 = load_immvalue(lb_c);
        val2 = load_immvalue(lb_c);
        val3 = load_immvalue(lb_c);
        break;
      case RNN:
        val1 = load_regvalue(lb_r, reg);
        break;
      case RRN:
        val1 = load_regvalue(lb_r, reg);
        val2 = load_regvalue(lb_r, reg);
        break;
      case RRI:
        val1 = load_regvalue(lb_r, reg);
        val2 = load_regvalue(lb_r, reg);
        val3 = load_immvalue(lb_c);
        break;
      case RRR:
        val1 = load_regvalue(lb_r, reg);
        val2 = load_regvalue(lb_r, reg);
        val3 = load_regvalue(lb_r, reg);
        break;
      case RII:
        val1 = load_regvalue(lb_r, reg);
        val2 = load_immvalue(lb_c);
        val3 = load_immvalue(lb_c);
        break;
      case RIR:
        val1 = load_regvalue(lb_r, reg);
        val2 = load_immvalue(lb_c);
        val3 = load_regvalue(lb_r, reg);
        break;
      case RIN:
        val1 = load_regvalue(lb_r, reg);
        val2 = load_immvalue(lb_c);
        break;
      default:
        fprintf(stderr, "Invalid flag: %d.\n", flag);
        exit(EXIT_FAILURE);
    }

    instruction_execute(&ret, opcode, val1, val2, val3);
    reg[dst] = ret;
  }
}

/******************************************************************************
 *                        SE APIs
 ******************************************************************************/
void SEstart(u8 *esharedkey,
             u8 *execID,
             u8 *Cin,
             u8 *header, u32 lb_m,
             u8 *hash)
{
  // execution identity: E_ID
  u32 header_inbytes = CT_SEPUB_INBYTES+lb_m;
  u8 msg[HASH_INBYTES+header_inbytes];
  memcpy(msg, hash, HASH_INBYTES);
  memcpy(msg+HASH_INBYTES, header, header_inbytes);
  hash_withprefix(execID, 0, msg, HASH_INBYTES + header_inbytes);

  // (C_H, n) <- header
  // K_S
  u8 shared_key[SHAREDKEY_INBYTES];
  int ret = crypto_box_seal_open(shared_key, header, CT_SEPUB_INBYTES, pubkey, prvkey);
  if (ret != 0){
    fprintf(stderr, "SEstart: Authenticated decryption header failed.\n");
    exit(EXIT_FAILURE);
  }

  // encrypt shared_key: E_K
  u8 nonce[NONCE_INBYTES];
  hash_withprefix(nonce, 1, execID, HASH_INBYTES);
  u64 clen;
  crypto_aead_encrypt(esharedkey, &clen,
                      shared_key, SHAREDKEY_INBYTES,
                      NULL, 0,
                      NULL, nonce,
                      seckey);
  if (clen != ENCRYPTED_SHAREDKEY_INBYTES){
    fprintf(stderr, "SEstart: Encrypting shared key failed.\n");
    exit(EXIT_FAILURE);
  }

  // L = ceil(n/l_out)
  u32 n = load_u32(header+CT_SEPUB_INBYTES, lb_m);
  u32 L = (n + l_out - 1) / l_out;
  u8 Lbstr[U32_INBYTES];
  u32_tobytes(Lbstr, U32_INBYTES, L);

  // C_L^in
  u8 ad[AIN_INBYTES];
  memcpy(ad, hash, HASH_INBYTES);
  memcpy(ad+HASH_INBYTES, Lbstr, U32_INBYTES);
  memcpy(ad+HASH_INBYTES+U32_INBYTES, execID, HASH_INBYTES);

  memcpy(msg, execID, HASH_INBYTES);
  memcpy(msg+HASH_INBYTES, Lbstr, U32_INBYTES);

  hash_withprefix(nonce, 2, msg, HASH_INBYTES+U32_INBYTES);

  crypto_aead_encrypt(Cin, &clen,
                      NULL, 0,
                      ad, AIN_INBYTES,
                      NULL, nonce,
                      seckey);
  if (clen != CIN_INBYTES){
    fprintf(stderr, "SEstart: Encrypting Cin failed.\n");
    exit(EXIT_FAILURE);
  }
}

void SEinput(u8 *Cinp,
             EWORD *C,
             u8 *execID,
             u32 i,
             u8 *Hp,
             uSE *X,
             u8 *Cinc)
// X : aka X_i
// Cinp: previous Cin, aka C_{i-1}^in
// Cinc: current Cin, aka C_i^in
// Hp: previous hash, aka H_{i-1}
// Hc: current hash, aka H_i
{
  if (i < 1){
    fprintf(stderr, "SEinput: Check i failed.\n");
    exit(EXIT_FAILURE);
  }
  u32 j;
  if (i == 1){
    u32 sum = 0;
    for(j=0; j<HASH_INBYTES; j++) sum += Hp[j];
    if (sum != 0){
      fprintf(stderr, "SEinput: Check H_0 when i=1 failed.\n");
      exit(EXIT_FAILURE);
    }
  }

  // H_i
  u8 Hc[HASH_INBYTES];
  hashchain(Hc, Hp, X);

  // A_i^in
  u8 ibstr[U32_INBYTES];
  u32_tobytes(ibstr, U32_INBYTES, i);
  u8 ad[AIN_INBYTES];
  memcpy(ad, Hc, HASH_INBYTES);
  memcpy(ad+HASH_INBYTES, ibstr, U32_INBYTES);
  memcpy(ad+HASH_INBYTES+U32_INBYTES, execID, HASH_INBYTES);

  // N_i^in
  u8 nonce[NONCE_INBYTES];
  u8 msg[HASH_INBYTES+U32_INBYTES];
  memcpy(msg, execID, HASH_INBYTES);
  memcpy(msg+HASH_INBYTES, ibstr, U32_INBYTES);
  hash_withprefix(nonce, 2, msg, HASH_INBYTES+U32_INBYTES);

  // ADec
  u8 *m = NULL;
  u64 mlen;

  int ret = crypto_aead_decrypt(m, &mlen,
                                NULL,
                                Cinc, CIN_INBYTES,
                                ad, AIN_INBYTES,
                                nonce, seckey);

  if (ret != 0 || mlen != 0){
    fprintf(stderr, "SEinput: Decrypting Cin failed.\n");
    exit(EXIT_FAILURE);
  }

  // N_{i-1}^in
  u8 pbstr[U32_INBYTES];
  u32_tobytes(pbstr, U32_INBYTES, i-1);
  memcpy(msg+HASH_INBYTES, pbstr, U32_INBYTES);
  hash_withprefix(nonce, 2, msg, HASH_INBYTES+U32_INBYTES);
  // A_{i-1}^in
  memcpy(ad, Hp, HASH_INBYTES);
  memcpy(ad+HASH_INBYTES, pbstr, U32_INBYTES);
  // C_{i-1}^in
  u64 clen;
  crypto_aead_encrypt(Cinp, &clen,
                      NULL, 0,
                      ad, AIN_INBYTES,
                      NULL,
                      nonce, seckey);
  // C_{i,1}, ..., C_{i,l_out}
  u8 jbstr[U32_INBYTES];
  u8 bword[WORD_INBYTES];
  memcpy(ad, ibstr, U32_INBYTES);
  memcpy(ad+2*U32_INBYTES, execID, HASH_INBYTES);
  for(j=0; j<l_out; j++){
    // A_{i,j}
    u32_tobytes(jbstr, U32_INBYTES, j);
    memcpy(ad+U32_INBYTES, jbstr, U32_INBYTES);
    // N_{i,j}
    hash_withprefix(nonce, 3, ad, A_INBYTES);
    // X_{i,j}
    word_tobytes(bword, X[j]);
    // C_{i,j}
    crypto_aead_encrypt(C[j].eword, &clen,
                        bword, U32_INBYTES,
                        ad, A_INBYTES,
                        NULL,
                        nonce, seckey);
    if (clen != C_INBYTES){
      fprintf(stderr, "SEinput: Encrypting word (C) failed.\n");
      exit(EXIT_FAILURE);
    }
  }
}

void SEeval(EWORD *Cr,
            u8 *execID,
            u8 *esharedkey,
            AELLS *aells,
            EWORD *Cx,
            u32 r,
            u32 lb_m,
            u32 lb_r,
            u32 lb_c,
            u32 lb_o)
// Cx: encrypted input words
// Cr: encrypted output words
{
  // decrypt shared_key K_S
  u8 shared_key[SHAREDKEY_INBYTES];
  u8 nonce[NONCE_INBYTES];
  u64 mlen;
  hash_withprefix(nonce, 1, execID, HASH_INBYTES);
  int ret = crypto_aead_decrypt(shared_key, &mlen,
                                NULL,
                                esharedkey, ENCRYPTED_SHAREDKEY_INBYTES,
                                NULL, 0,
                                nonce, seckey);
  if (ret != 0 || mlen != SHAREDKEY_INBYTES){
    fprintf(stderr, "SEeval: Authenticated decrypting shared_key failed.\n");
    exit(EXIT_FAILURE);
  }

  // decrypt instructions f_\nu
  u32 lls_bytelen = aells->bytelen-MAC_INBYTES;
  u8 *lls_bytecode = malloc(lls_bytelen);
  LLS_decrypt(lls_bytecode, aells, shared_key, lb_m, lb_o);

  // register
  uSE *reg = malloc(r * sizeof(uSE));

  // decrypt encrypted input words Cx and store them into register
  EWORD_decrypt(reg, aells, execID, Cx);

  // execute instructions
  LLS_execute(reg, lls_bytecode, lls_bytelen, lb_c, lb_r);

  // output words in clear
  if (aells->reveal_flag) EWORD_encode(Cr, aells, reg, r);
  // encrypt output words
  else EWORD_encrypt(Cr, aells, execID, reg, r);

  free(lls_bytecode);
  free(reg);
}