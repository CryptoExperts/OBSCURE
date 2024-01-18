#ifndef MULTI_INSTRUCTION_H
#define MULTI_INSTRUCTION_H

typedef unsigned int u32;
typedef unsigned char u8;

// This corresponds to (i,j) of the ID_in
typedef struct _ID {
  u32 instrID;
  u32 outputID;
} ID;

// Authenticated-Encrypted Low-Level Snippet
// This will be data sent to the SE to execute a multi-instruction
typedef struct _AELLS
{
  u8  reveal_flag;
  u32 inp_count;  // copy from LLMI
  u32 out_count;  // copy from LLMI
  ID  *inputIDs;
  u32 instrID;
  u32 bytelen;
  u8  *bytecode;  // encrypted instructions
} AELLS;


typedef struct _LLMI
{
  u32 inp_count;
  u32 out_count;
  u32 *mem_inps;
  u32 *mem_outs;
  AELLS aells;
} LLMI;

// Encrypted word
typedef struct _EWORD
{
  u8 eword[C_INBYTES];
} EWORD;

#endif