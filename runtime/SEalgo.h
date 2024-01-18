#ifndef SEALGO_H
#define SEALGO_H

#include "crypto_uint.h"
#include "crypto_len.h"
#include "multi_instruction.h"

void SEstart(u8 *esharedkey,
             u8 *execID,
             u8 *Cin,
             u8 *header, u32 lb_m,
             u8 *hash);

void SEinput(u8 *Cinp,
             EWORD *C,
             u8 *execID,
             u32 i,
             u8 *Hp,
             uSE *X,
             u8 *Cinc);

void SEeval(EWORD *Cr,
            u8 *execID,
            u8 *esharedkey,
            AELLS *aells,
            EWORD *Cx,
            u32 r,
            u32 lb_m,
            u32 lb_r,
            u32 lb_c,
            u32 lb_o);

#endif