#ifndef UTILS_H
#define UTILS_H

#include "crypto_uint.h"

void word_tobytes(u8 *bytes, uSE x);
uSE load_word(u8 *bytes, u32 bytelen);
u32 load_u32(const u8* bytes, u32 bytelen);
void u32_tobytes(u8 *bytes, u32 bytelen, u32 num);
void batch_tobytes(u8 *Xbstr, uSE* X);

void hashchain(u8 *Hc, u8 *Hp, uSE* X);

#endif // UTILS_H


