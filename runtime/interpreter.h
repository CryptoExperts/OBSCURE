#ifndef INTERPRETER_H
#define INTERPRETER_H

#include "SEconfig.h"
#include "crypto_uint.h"


void interpret(u8  *bytecode, unsigned long bytecode_len,
               uSE *prog_inps, u32 prog_inpcount,
               uSE *prog_outs, u32 prog_outcount);

#endif
