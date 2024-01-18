#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

void key_sched(unsigned char out[176], const unsigned char in[16]);
void AES_K(unsigned int c[8], const unsigned int m[8]);
void AES_T(unsigned int c[8], const unsigned int m[8]);
void tracing_AES(unsigned int c[8], const unsigned int m[8]);

static void transpose(unsigned char data[8]) {
  unsigned char mask_l[3] = { 0xaa, 0xcc, 0xf0 };
  unsigned char mask_r[3] = { 0x55, 0x33, 0x0f };

  for (int i = 0; i < 3; i ++) {
    int n = (1UL << i);
    for (int j = 0; j < 8; j += (2 * n))
      for (int k = 0; k < n; k ++) {
        unsigned char u = data[j + k] & mask_l[i];
        unsigned char v = data[j + k] & mask_r[i];
        unsigned char x = data[j + n + k] & mask_l[i];
        unsigned char y = data[j + n + k] & mask_r[i];
        data[j + k] = u | (x >> n);
        data[j + n + k] = (v << n) | y;
      }
  }
}

static void reorder(unsigned char data[16]) {
  unsigned char tmp[16];
  memcpy(tmp,data,16);
  unsigned char pattern[16] = { 0, 4,  8, 12,
                          1, 5,  9, 13,
                          2, 6, 10, 14,
                          3, 7, 11, 15 };
  for (int i = 0; i < 16; i++)
    data[i] = tmp[pattern[i]];
}

static void fromuchar2uint(unsigned int *out, unsigned char *in, unsigned int inlen)
{
  unsigned int i, j;
  for (i = 0; i < inlen/16; i++){
    for (j = 0; j < 8; j++){
      out[i*8+j] = ((unsigned int) in[i*16+j] << 8) | ((unsigned int) in[i*16+j+8] & 0xff);
    }
  }
}

static void fromuint2uchar(unsigned char *out, unsigned int *in, unsigned int inlen)
{
  unsigned int i, j;
  for (i = 0; i < inlen/8; i++){
    for (j = 0; j < 8; j++){
      out[i*16+j]   = in[i*8+j] >> 8;
      out[i*16+j+8] = in[i*8+j] & 0xff;
    }
  }
}

static void unittest(unsigned char* m, const unsigned char* expected, const unsigned int is_pertub)
{
  reorder(m);
  transpose(m);
  transpose(m+8);
  unsigned int m1[8];
  fromuchar2uint(m1, m, 16);
  unsigned int c1[8];
  tracing_AES(c1, m1);

  unsigned char c[16];
  fromuint2uchar(c, c1, 8);
  transpose(c);
  transpose(c+8);
  reorder(c);

  if ((memcmp(expected, c, 16) != 0) ^ is_pertub){
    fprintf(stderr, "Error!\n");
    fprintf(stderr, "Expected: ");
    unsigned int i;
    for (i = 0; i < 16; i++) fprintf(stderr, "%02x ", expected[i]); fprintf(stderr, "\n");
    fprintf(stderr, "Returned: ");
    for (i = 0; i < 16; i++) fprintf(stderr, "%02x", c[i]); fprintf(stderr, "\n");
  }
  else {
    fprintf(stdout, "OK\n");
  }
}

int main()
{
  // This implementation is encryption (instead of decryption)
  // USER ID is 4 (harcoded in tracing AES)
  // Below are 4 tracing plaintexts
  unsigned char tm3[16]      = {0x8e, 0x36, 0x3a, 0x62, 0x26, 0x94, 0xc4, 0x2c, 0x9f, 0x8a, 0x63, 0xf5, 0x32, 0x64, 0x79, 0xf6};
  unsigned char tm2[16]      = {0xb3, 0xc9, 0x98, 0x3c, 0x04, 0x49, 0x7c, 0x5e, 0x85, 0xd3, 0x35, 0x05, 0xc4, 0x6b, 0x19, 0x1a};
  unsigned char tm1[16]      = {0x19, 0xa1, 0x6e, 0xaa, 0x21, 0x64, 0x4c, 0x29, 0x2e, 0x55, 0x25, 0x90, 0x10, 0xe8, 0x16, 0x6f};
  unsigned char tm0[16]      = {0xad, 0xb6, 0x37, 0x51, 0x4c, 0xca, 0x39, 0x92, 0x24, 0x2c, 0xd8, 0xb7, 0x5d, 0xbd, 0x0a, 0xd5};
  unsigned char te0[16]      = {0xc0, 0x18, 0x0f, 0x85, 0xb6, 0xff, 0xa5, 0xd5, 0xac, 0x1d, 0x96, 0x73, 0x0e, 0xd9, 0x3d, 0x44};
  unsigned char te1[16]      = {0xf0, 0x64, 0xbf, 0x92, 0x79, 0xfb, 0x5d, 0x7b, 0xf5, 0x98, 0x4a, 0x1b, 0x29, 0xe7, 0xc6, 0xe9};
  unsigned char te2[16]      = {0xa1, 0xdf, 0xdf, 0x8b, 0xb9, 0xfd, 0xa9, 0x6f, 0xdb, 0x80, 0xba, 0x47, 0x04, 0x5f, 0xa4, 0xc1};
  unsigned char te3[16]      = {0xd0, 0x37, 0x01, 0xfd, 0xec, 0x59, 0x1b, 0x7a, 0x9c, 0xc7, 0xf3, 0x60, 0x1f, 0x57, 0xc8, 0xb3};
  // Tracing key (round keys are harcoded in tracing AES)
  unsigned char tk[16]       = {0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6, 0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c};
  // Main key (round keys are harcoded in tracing AES)
  unsigned char k[16]        = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f};
  // Test vector from NIST docs
  unsigned char m[16]        = {0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff};
  unsigned char e[16]        = {0x69, 0xc4, 0xe0, 0xd8, 0x6a, 0x7b, 0x04, 0x30, 0xd8, 0xcd, 0xb7, 0x80, 0x70, 0xb4, 0xc5, 0x5a};

  // unsigned int i;
  // // Rearrange bits of round keys to adapt bitslicing implementation
  // unsigned char ks[176];
  // key_sched(ks, tk);
  // for (i = 0; i < 11; i++){
  //   reorder(ks+i*16);
  //   transpose(ks+i*16);
  //   transpose(ks+i*16+8);
  // }
  // unsigned int ks1[88];
  // fromuchar2uint(ks1, ks, 176);

  unittest(m, e, 0);
  unittest(tm0, te0, 1);
  unittest(tm1, te1, 1);
  unittest(tm2, te2, 1);
  unittest(tm3, te3, 1);

  return 0;
}
