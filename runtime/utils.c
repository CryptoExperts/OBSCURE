#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "crypto_len.h"
#include "sparkle/esch/esch.h"
#include "utils.h"

u32 load_u32(const u8* bytes, u32 bytelen)
// big-endian
{
  u32 n;
  switch (bytelen){
    case 1:
      n = bytes[0];
      break;
    case 2:
      n = ((u32) bytes[0] << 8)
        | ((u32) bytes[1]     );
      break;
    case 3:
      n = ((u32) bytes[0] << 16)
        | ((u32) bytes[1] <<  8)
        | ((u32) bytes[2]      );
      break;
    case 4:
      n = ((u32) bytes[0] << 24)
        | ((u32) bytes[1] << 16)
        | ((u32) bytes[2] <<  8)
        | ((u32) bytes[3]      );
      break;
    default:
      fprintf(stderr, "Invalid number of bytes (%d).\n", bytelen);
      exit(EXIT_FAILURE);
    }
  return n;
}

u64 load_u64(const u8* bytes, u32 bytelen)
// big-endian
{
  u64 n;
  switch (bytelen){
    case 1:
      n = bytes[0];
      break;
    case 2:
      n = ((u64) bytes[0] << 8)
        | ((u64) bytes[1]     );
      break;
    case 3:
      n = ((u64) bytes[0] << 16)
        | ((u64) bytes[1] <<  8)
        | ((u64) bytes[2]      );
      break;
    case 4:
      n = ((u64) bytes[0] << 24)
        | ((u64) bytes[1] << 16)
        | ((u64) bytes[2] <<  8)
        | ((u64) bytes[3]      );
      break;
    case 5:
      n = ((u64) bytes[0] << 32)
        | ((u64) bytes[1] << 24)
        | ((u64) bytes[2] << 16)
        | ((u64) bytes[3] <<  8)
        | ((u64) bytes[4]      );
      break;
    case 6:
      n = ((u64) bytes[0] << 40)
        | ((u64) bytes[1] << 32)
        | ((u64) bytes[2] << 24)
        | ((u64) bytes[3] << 16)
        | ((u64) bytes[4] <<  8)
        | ((u64) bytes[5]      );
      break;
    case 7:
      n = ((u64) bytes[0] << 48)
        | ((u64) bytes[1] << 40)
        | ((u64) bytes[2] << 32)
        | ((u64) bytes[3] << 24)
        | ((u64) bytes[4] << 16)
        | ((u64) bytes[5] <<  8)
        | ((u64) bytes[6]      );
      break;
    case 8:
      n = ((u64) bytes[0] << 56)
        | ((u64) bytes[1] << 48)
        | ((u64) bytes[2] << 40)
        | ((u64) bytes[3] << 32)
        | ((u64) bytes[4] << 24)
        | ((u64) bytes[5] << 16)
        | ((u64) bytes[6] <<  8)
        | ((u64) bytes[7]      );
      break;
    default:
      fprintf(stderr, "Invalid number of bytes (%d).\n", bytelen);
      exit(EXIT_FAILURE);
    }
  return n;
}

void u32_tobytes(u8 *bytes, u32 bytelen, u32 num)
{
	switch (bytelen){
    case 1:
      bytes[0] = num;
      break;
    case 2:
      bytes[0] = num >>  8;
      bytes[1] = num      ;
      break;
    case 3:
      bytes[0] = num >> 16;
      bytes[1] = num >>  8;
      bytes[2] = num      ;
      break;
    case 4:
      bytes[0] = num >> 24;
      bytes[1] = num >> 16;
      bytes[2] = num >>  8;
      bytes[3] = num      ;
      break;
    default:
      fprintf(stderr, "Invalid bytelen: %d.\n", bytelen);
      exit(EXIT_FAILURE);
	}
}

void u64_tobytes(u8 *bytes, u32 bytelen, u64 num)
{
	switch (bytelen){
    case 1:
      bytes[0] = num;
      break;
    case 2:
      bytes[0] = num >>  8;
      bytes[1] = num      ;
      break;
    case 3:
      bytes[0] = num >> 16;
      bytes[1] = num >>  8;
      bytes[2] = num      ;
      break;
    case 4:
      bytes[0] = num >> 24;
      bytes[1] = num >> 16;
      bytes[2] = num >>  8;
      bytes[3] = num      ;
      break;
    case 5:
      bytes[0] = num >> 32;
      bytes[1] = num >> 24;
      bytes[2] = num >> 16;
      bytes[3] = num >>  8;
      bytes[4] = num      ;
      break;
    case 6:
      bytes[0] = num >> 40;
      bytes[1] = num >> 32;
      bytes[2] = num >> 24;
      bytes[3] = num >> 16;
      bytes[4] = num >>  8;
      bytes[5] = num      ;
      break;
    case 7:
      bytes[0] = num >> 48;
      bytes[1] = num >> 40;
      bytes[2] = num >> 32;
      bytes[3] = num >> 24;
      bytes[4] = num >> 16;
      bytes[5] = num >>  8;
      bytes[6] = num      ;
      break;
    case 8:
      bytes[0] = num >> 56;
      bytes[1] = num >> 48;
      bytes[2] = num >> 40;
      bytes[3] = num >> 32;
      bytes[4] = num >> 24;
      bytes[5] = num >> 16;
      bytes[6] = num >>  8;
      bytes[7] = num      ;
      break;
    default:
      fprintf(stderr, "Invalid bytelen: %d.\n", bytelen);
      exit(EXIT_FAILURE);
	}
}

void word_tobytes(u8 *bytes, uSE x)
{
  switch (WORD_SIZE){
    case 32:
      u32_tobytes(bytes, WORD_SIZE/8, x);
      break;
    case 64:
      u64_tobytes(bytes, WORD_SIZE/8, x);
      break;
    default:
      fprintf(stderr, "Unsupported WORD_SIZE: %d.\n", WORD_SIZE);
      exit(EXIT_FAILURE);
  }
}

uSE load_word(u8 *bytes, u32 bytelen)
{
  switch (WORD_SIZE){
    case 32:
      return load_u32(bytes, bytelen);
    case 64:
      return load_u64(bytes, bytelen);
    default:
      fprintf(stderr, "Unsupported WORD_SIZE: %d.\n", WORD_SIZE);
      exit(EXIT_FAILURE);
  }
}

void batch_tobytes(u8 *Xbstr, uSE* X)
{
  u8 *ptr = Xbstr;
  u32 i;
  switch (WORD_SIZE){
    case 32:
      for (i=0; i<l_out; i++){
        u32_tobytes(ptr, 4, X[i]);
        ptr += 4;
      }
      break;
    case 64:
      for (i=0; i<l_out; i++){
        u64_tobytes(ptr, 8, X[i]);
        ptr += 8;
      }
      break;
    default:
      fprintf(stderr, "Unsupported WORD_SIZE: %d.\n", WORD_SIZE);
      exit(EXIT_FAILURE);
  }
}

void hashchain(u8 *Hc, u8 *Hp, uSE* X)
// Hc: current H, Hp: previous H, X: batch
// Hc = Hash(Hp, X)
{
  u64 mlen = HASH_INBYTES + BATCH_INBYTES;
  u8 msg[mlen];
  u8 Xbstr[BATCH_INBYTES];

  batch_tobytes(Xbstr, X);
  memcpy(msg, Hp, HASH_INBYTES);
  memcpy(msg + HASH_INBYTES, Xbstr, BATCH_INBYTES);
  crypto_hash(Hc, msg, mlen);
}