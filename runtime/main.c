
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <getopt.h>
#include "interpreter.h"


static int is_int(char* s) {
  if (!s || !*s) return 0;
  while (*s) {
    if (*s < '0' || *s > '9') return 0;
    s++;
  }
  return 1;
}

static int to_int(char* opt_name, char* provided) {
  if (!is_int(provided)) {
    fprintf(stderr, "Option -%s expacts an integer. Provided: '%s'. Exiting\n",
            opt_name, provided);
    exit(EXIT_FAILURE);
  }
  return strtol(provided, NULL, 0);
}

static int count_char(char* str, char c) {
  int count = 0;
  for (; *str != '\0'; str++) {
    count += *str == c;
  }
  return count;
}

static uSE* parse_inputs(char* str, int* input_count) {
  *input_count = count_char(str, ',')+1;
  uSE* inputs = malloc(*input_count * sizeof(*inputs));
  int count = 0;
  char* token = strtok(str, ",");
  while (token != NULL) {
    if (is_int(token)) {
      inputs[count++] = to_int("-inputs", token);
    }
    token = strtok(NULL, ",");
  }
  return inputs;
}


char* prog_name = NULL;
static void usage() {
  fprintf(stderr, "Usage:\n"
          "    %s BYTECODE_FILE\n"
          "Inteprets the BYTECODE_FILE with the provided configuration arguments.\n\n"
          "Mandatory arguments:\n"
          "Optional arguments:\n"
          "    --inputs INT_LIST        inputs to give the program (separated by commas)\n",
          "    --out_count INT          number of outputs for the program\n",
          prog_name);
  exit(EXIT_FAILURE);
}

#define INPUTS_OPT 1000
#define OUT_COUNT_OPT 1001

int main(int argc, char** argv) {
  prog_name = argv[0];

  // Parsing options
  char* filename = NULL;
  uSE* inputs = NULL;
  int input_count = -1;
  int output_count = 1;

  while (1) {
    static struct option long_options[] = {
      { "help",   no_argument,       0, 'h' },
      { "inputs", required_argument, 0, INPUTS_OPT },
      { "out_count", required_argument, 0, OUT_COUNT_OPT },
      { NULL, 0, NULL, 0 }
    };

    int option_index = 0;
    int c = getopt_long(argc, argv, "h", long_options, &option_index);

    if (c == -1) break;

    switch (c) {
    case 'h':
      usage();
      break;
    case INPUTS_OPT:
      inputs = parse_inputs(optarg, &input_count);
      break;
    case OUT_COUNT_OPT:
      output_count = to_int("out_count", optarg);
      break;
    default:
      usage();
    }
  }

  if (!inputs) {
    fprintf(stderr, "Missing mandatory argument.\n\n");
    usage();
  }

  while (optind < argc) {
    if (filename) {
      fprintf(stderr, "I don't know what to do with extra argument '%s'.\n\n", argv[optind]);
      usage();
    }
    filename = argv[optind];
    optind++;
  }

  if (!filename) {
    fprintf(stderr, "Missing argument: no bytecode file provided.\n\n");
    usage();
  }


  // Reading bytecode
  FILE* f = fopen(filename, "rb");
  if (! f) {
    fprintf(stderr, "Cannot open '%s': ", filename);
    perror("");
    exit(EXIT_FAILURE);
  }
  fseek(f, 0, SEEK_END);
  unsigned long bytecode_length = ftell(f);
  fseek(f, 0, SEEK_SET);
  unsigned char* bytecode = malloc(bytecode_length);
  fread(bytecode, 1, bytecode_length, f);
  fclose(f);

  // Interpreting bytecode
  uSE* outputs = malloc(output_count * sizeof(*outputs));
  interpret(bytecode, bytecode_length, \
            inputs,  (u32) input_count, \
            outputs, (u32) output_count);

  // Print outputs
  for (int i = 0; i < output_count; i++){
    fprintf(stdout, "%u\n", outputs[i]);
  }

  // Free memory
  free(inputs);
  free(outputs);
  free(bytecode);
}
