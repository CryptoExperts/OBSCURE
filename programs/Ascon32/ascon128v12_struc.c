#define ASCON_AEAD_RATE 8
#define WORD_SIZE 4
#define PAD0o 2147483648
#define PAD0e 0

unsigned int deinterleave_uint32(unsigned int x) {
  unsigned int t;
  t = (x ^ (x >> 1)) & 0x22222222; x ^= t ^ (t << 1);
  t = (x ^ (x >> 2)) & 0x0C0C0C0C; x ^= t ^ (t << 2);
  t = (x ^ (x >> 4)) & 0x00F000F0; x ^= t ^ (t << 4);
  t = (x ^ (x >> 8)) & 0x0000FF00; x ^= t ^ (t << 8);
  return x;
}

unsigned int interleave_uint32(unsigned int x) {
  unsigned int t;
  t = (x ^ (x >> 8)) & 0x0000FF00; x ^= t ^ (t << 8);
  t = (x ^ (x >> 4)) & 0x00F000F0; x ^= t ^ (t << 4);
  t = (x ^ (x >> 2)) & 0x0C0C0C0C; x ^= t ^ (t << 2);
  t = (x ^ (x >> 1)) & 0x22222222; x ^= t ^ (t << 1);
  return x;
}

static void deinterleave32(unsigned int out[2],
                     const unsigned int in[2]) {
  unsigned int hi = in[1];
  unsigned int lo = in[0];
  unsigned int r0, r1;
  lo = deinterleave_uint32(lo);
  hi = deinterleave_uint32(hi);
  r0 = (lo & 0x0000FFFF) | (hi << 16);
  r1 = (lo >> 16) | (hi & 0xFFFF0000);
  out[0] = r1;
  out[1] = r0;
}

static void interleave32(unsigned int out[2],
                    const unsigned int in[2]) {
  unsigned int r0 = in[1];
  unsigned int r1 = in[0];
  unsigned int lo = (r0 & 0x0000FFFF) | (r1 << 16);
  unsigned int hi = (r0 >> 16) | (r1 & 0xFFFF0000);
  lo = interleave_uint32(lo);
  hi = interleave_uint32(hi);
  out[0] = lo;
  out[1] = hi;
}

static void U64BIG(unsigned int out[2],
             const unsigned int in[2]){
  out[0] =  ((in[1] & 0x000000ff) << 24) |
            ((in[1] & 0x0000ff00) << 8 ) |
            ((in[1] & 0x00ff0000) >> 8 ) |
            ((in[1] & 0xff000000) >> 24);
  out[1] =  ((in[0] & 0x000000ff) << 24) |
            ((in[0] & 0x0000ff00) << 8 ) |
            ((in[0] & 0x00ff0000) >> 8 ) |
            ((in[0] & 0xff000000) >> 24);
}

static void LOAD(unsigned int out[2],
           const unsigned int in[2]){
  unsigned int x[2];
  U64BIG(x, in);
  deinterleave32(out, x);
}

static void STORE(unsigned int out[2],
            const unsigned int in[2]){
  unsigned int x[2];
  interleave32(x, in);
  U64BIG(out, x);
}

unsigned int ROR32(unsigned int x, unsigned int n) {
  unsigned int c = ((n - 1) >> 8) & 1;

  unsigned int X = x;
  unsigned int Y = x >> n | x << (32 - n);
  return c ? X : Y;
}

unsigned int RORe(unsigned int o,
                  unsigned int e,
                  unsigned int n) {
  unsigned int c = n % 2;
  unsigned int X = ROR32(o, (n - 1) / 2);
  unsigned int Y = ROR32(e, n / 2);
  return c ? X : Y;
}

unsigned int RORo(unsigned int o,
                  unsigned int e,
                  unsigned int n) {
  unsigned int c = n % 2;
  unsigned int X = ROR32(e, (n + 1) / 2);
  unsigned int Y = ROR32(o, n / 2);
  return c ? X : Y;
}

unsigned int NOTZERO(unsigned int ao,
            unsigned int ae,
            unsigned int bo,
            unsigned int be) {
  unsigned int result = ae | ao | be | bo;
  result |= result >> 16;
  result |= result >> 8;
  return ((((result & 0xff) - 1) >> 8) & 1) - 1;
}

#define ASCON_128_IV_0 2149646336
#define ASCON_128_IV_1 136445952

static void ROUND(unsigned int* s,
                  unsigned int Ce,
                  unsigned int Co) {
  unsigned int t[10];
  /* round constant */
  // s->x2
  s[4] ^= Co; s[5] ^= Ce;
  /* s-box layer */
  // s->x0
  s[0] ^= s[8]; s[1] ^= s[9];
  // s->x4
  s[8] ^= s[6]; s[9] ^= s[7];
  // s->x2
  s[4] ^= s[2]; s[5] ^= s[3];
  // t->x0
  t[0] = s[0] ^ (~s[2] & s[4]); t[1] = s[1] ^ (~s[3] & s[5]);
  // t->x2
  t[4] = s[4] ^ (~s[6] & s[8]); t[5] = s[5] ^ (~s[7] & s[9]);
  // t->x4
  t[8] = s[8] ^ (~s[0] & s[2]); t[9] = s[9] ^ (~s[1] & s[3]);
  // t->x1
  t[2] = s[2] ^ (~s[4] & s[6]); t[3] = s[3] ^ (~s[5] & s[7]);
  // t->x3
  t[6] = s[6] ^ (~s[8] & s[0]); t[7] = s[7] ^ (~s[9] & s[1]);
  // t->x1
  t[2] ^= t[0]; t[3] ^= t[1];
  // t->x3
  t[6] ^= t[4]; t[7] ^= t[5];
  // t->x0
  t[0] ^= t[8]; t[1] ^= t[9];
  /* linear layer */
  // s->x2
  s[4] = t[4] ^ RORo(t[4], t[5], 6-1);
  s[5] = t[5] ^ RORe(t[4], t[5], 6-1);
  // s->x3
  s[6] = t[6] ^ RORo(t[6], t[7], 17-10);
  s[7] = t[7] ^ RORe(t[6], t[7], 17-10);
  // s->x4
  s[8] = t[8] ^ RORo(t[8], t[9], 41-7);
  s[9] = t[9] ^ RORe(t[8], t[9], 41-7);
  // s->x0
  s[0] = t[0] ^ RORo(t[0], t[1], 28-19);
  s[1] = t[1] ^ RORe(t[0], t[1], 28-19);
  // s->x1
  s[2] = t[2] ^ RORo(t[2], t[3], 61-39);
  s[3] = t[3] ^ RORe(t[2], t[3], 61-39);
  // s->x2
  unsigned int tx0, tx1;
  tx0 = s[4]; tx1 = s[5];
  s[4] = t[4] ^ RORo(tx0, tx1, 1);
  s[5] = t[5] ^ RORe(tx0, tx1, 1);
  // s->x3
  tx0 = s[6]; tx1 = s[7];
  s[6] = t[6] ^ RORo(tx0, tx1, 10);
  s[7] = t[7] ^ RORe(tx0, tx1, 10);
  // s->x4
  tx0 = s[8]; tx1 = s[9];
  s[8] = t[8] ^ RORo(tx0, tx1, 7);
  s[9] = t[9] ^ RORe(tx0, tx1, 7);
  // s->x0
  tx0 = s[0]; tx1 = s[1];
  s[0] = t[0] ^ RORo(tx0, tx1, 19);
  s[1] = t[1] ^ RORe(tx0, tx1, 19);
  // s->x1
  tx0 = s[2]; tx1 = s[3];
  s[2] = t[2] ^ RORo(tx0, tx1, 39);
  s[3] = t[3] ^ RORe(tx0, tx1, 39);
  // s->x2
  s[4] = ~s[4];
  s[5] = ~s[5];
}

static void P12(unsigned int* s) {
  ROUND(s, 0xc, 0xc);
  ROUND(s, 0x9, 0xc);
  ROUND(s, 0xc, 0x9);
  ROUND(s, 0x9, 0x9);
  ROUND(s, 0x6, 0xc);
  ROUND(s, 0x3, 0xc);
  ROUND(s, 0x6, 0x9);
  ROUND(s, 0x3, 0x9);
  ROUND(s, 0xc, 0x6);
  ROUND(s, 0x9, 0x6);
  ROUND(s, 0xc, 0x3);
  ROUND(s, 0x9, 0x3);
}

static void P6(unsigned int* s) {
  ROUND(s, 0x6, 0x9);
  ROUND(s, 0x3, 0x9);
  ROUND(s, 0xc, 0x6);
  ROUND(s, 0x9, 0x6);
  ROUND(s, 0xc, 0x3);
  ROUND(s, 0x9, 0x3);
}

static void ascon_aeadinit(unsigned int* s,
                     const unsigned int* npub,
                     const unsigned int* k) {
  /* load nonce */
  unsigned int N0[2], N1[2], in[2];
  in[0] = npub[0]; in[1] = npub[1];
  LOAD(N0, in);
  in[0] = npub[2]; in[1] = npub[3];
  LOAD(N1, in);
  /* load key */
  unsigned int K0[2], K1[2];
  in[0] = k[0]; in[1] = k[1];
  LOAD(K0, in);
  in[0] = k[2]; in[1] = k[3];
  LOAD(K1, in);
  /* initialize */
  unsigned int i;
  for (i = 0; i < 10; i++) s[i] = 0;
  // s->x0
  s[0] = ASCON_128_IV_0;
  s[1] = ASCON_128_IV_1;
  // s->x1
  s[2] = K0[0]; s[3] = K0[1];
  // s->x2
  s[4] = K1[0]; s[5] = K1[1];
  // s->x3
  s[6] = N0[0]; s[7] = N0[1];
  // s->x4
  s[8] = N1[0]; s[9] = N1[1];

  P12(s);

  // s->x3 = s->x3 ^ K0
  s[6] ^= K0[0]; s[7] ^= K0[1];
  // s->x4 = s->x4 ^ K1
  s[8] ^= K1[0]; s[9] ^= K1[1];
}

static void ascon_adata(unsigned int* s,
                  const unsigned int* ad,
                        unsigned int adlen) {
  /* full associated data blocks */
  unsigned int i, in[2], t[2];
  for (i = 0; i < adlen; i += 2) {
    // s->x0
    in[0] = ad[i]; in[1] = ad[i+1];
    LOAD(t, in);
    s[0] ^= t[0]; s[1] ^= t[1];
    P6(s);
  }
  /* final associated data block */
  s[0] ^= PAD0o; s[1] ^= PAD0e;
  P6(s);
  /* domain separation */
  s[8] ^= 0; s[9] ^= 1;
}

static void ascon_encrypt(unsigned int* s,
                          unsigned int* c,
                    const unsigned int* m,
                          unsigned int mlen) {
  /* full plaintext blocks */
  unsigned int i, in[2], t[2];
  for (i = 0; i < mlen; i += 2) {
    in[0] = m[i]; in[1] = m[i+1];
    LOAD(t, in);
    s[0] ^= t[0]; s[1] ^= t[1];
    STORE(t, s);
    c[i] = t[0]; c[i+1] = t[1];
    P6(s);
  }
  /* final plaintext block */
  s[0] ^= PAD0o; s[1] ^= PAD0e;
}

static void ascon_decrypt(unsigned int* s,
                          unsigned int* m,
                    const unsigned int* c,
                          unsigned int clen) {
  /* full ciphertext blocks */
  unsigned int i;
  unsigned int cx[2], in[2], t[2];
  for (i = 0; i < clen; i += 2) {
    in[0] = c[i]; in[1] = c[i+1];
    LOAD(cx, in);
    s[0] ^= cx[0]; s[1] ^= cx[1];
    STORE(t, s);
    m[i] = t[0];   m[i+1] = t[1];
    s[0] = cx[0]; s[1] = cx[1];
    P6(s);
  }
  /* final ciphertext block */
  s[0] ^= PAD0o; s[1] ^= PAD0e;
}

static void ascon_final(unsigned int* s,
                  const unsigned int* k) {
  /* load key */
  unsigned int K0[2], K1[2], in[2];
  in[0] = k[0]; in[1] = k[1];
  LOAD(K0, in);
  in[0] = k[2]; in[1] = k[3];
  LOAD(K1, in);
  /* finalize */
  // s->x1
  s[2] ^= K0[0]; s[3] ^= K0[1];
  // s->x2
  s[4] ^= K1[0]; s[5] ^= K1[1];
  P12(s);
  // s->x3
  s[6] ^= K0[0]; s[7] ^= K0[1];
  // s->x4
  s[8] ^= K1[0]; s[9] ^= K1[1];
}

int crypto_aead_encrypt_struc(unsigned int* c,
                        const unsigned int* m,
                        const unsigned int* ad,
                        const unsigned int* npub,
                        const unsigned int* k) {
  unsigned int mlen = 4;
  unsigned int adlen = 4;

  unsigned int s[10];
  /* perform ascon computation */
  ascon_aeadinit(s, npub, k);
  ascon_adata(s, ad, adlen);
  ascon_encrypt(s, c, m, mlen);
  ascon_final(s, k);
  // /* set tag */
  unsigned int t[2], in[2];
  in[0] = s[6]; in[1] = s[7];
  STORE(t, in);
  c[4] = t[0]; c[5] = t[1];
  in[0] = s[8]; in[1] = s[9];
  STORE(t, in);
  c[6] = t[0]; c[7] = t[1];
  return 0;
}

int crypto_aead_decrypt_struc(unsigned int* m,
                        const unsigned int* c,
                        const unsigned int* ad,
                        const unsigned int* npub,
                        const unsigned int* k) {
  unsigned int s[10];
  unsigned int adlen = 4;
  unsigned int clen = 4; // removed TAG

  /* perform ascon computation */
  ascon_aeadinit(s, npub, k);
  ascon_adata(s, ad, adlen);
  ascon_decrypt(s, m, c, clen);
  ascon_final(s, k);
  /* verify tag (should be constant time, check compiler output) */
  // s.x3
  unsigned int t[2], in[2];
  in[0] = c[4]; in[1] = c[5];
  LOAD(t, in);
  s[6] ^= t[0]; s[7] ^= t[1];
  in[0] = c[6]; in[1] = c[7];
  LOAD(t, in);
  s[8] ^= t[0]; s[9] ^= t[1];

  return NOTZERO(s[6], s[7], s[8], s[9]);
}
