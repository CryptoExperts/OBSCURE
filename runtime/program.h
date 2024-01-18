#ifndef PROGRAM_H
#define PROGRAM_H

#include "multi_instruction.h"

typedef unsigned int u32;

typedef struct _Program
{
  u32 inp_count;
  u32 out_count;
  u32 *mem_inps;
  u32 *mem_outs;
  u32 llmi_count;
  LLMI *llmis;

} Program;

#endif