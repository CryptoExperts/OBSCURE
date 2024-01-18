// Note that this file doesn't end with .c or .info, so it's ignored
// by the testing script. Still, it contains valid C code, and is
// actually the TinyJambu cipher before applying CPP.

// To "clean" to be able to compile:
//   - remove either crypto_aead_encrypt_struc or crypto_aead_decrypt_struc
//   - run "cpp -P TinyJampu.beforeCPP -o TinyJambu.c"

/*
     TinyJAMBU-128: 128-bit key, 96-bit IV
     Reference implementation for 32-bit CPU
     The state consists of four 32-bit registers
     state[3] || state[2] || state[1] || state[0]

     Implemented by: Hongjun Wu
*/


/* Modofications compared to original:
   - removed two "if" (whose condition depended on adlen and mlen)
   - removed clen parameter
   - fixed mlen to 16 (and removed param)
   - fixed adlen to 16 (and removed param adlen)
   - change type of pointers to "unsigned int*" instead of "unsigned char*"
      + removed "unsigned int*" casts
      + changed number of iterations of final loop to 2 instead of 8,
        and used (mlen >> 2) instead of mlen in this loop
        (for (j = 0; j < 2; j++) c[(mlen>>2)+j] = mac[j];)
        because "c" and "mac" are now "unsigned int*" instead of "unsigned char*"
   - changed all scalar types to "unsigned int"
   - removed unused parameter nsec
 */


#define FrameBitsIV 0x10
#define FrameBitsAD 0x30
#define FrameBitsPC 0x50 // Framebits for plaintext/ciphertext
#define FrameBitsFinalization 0x70

#define NROUND1 128 * 5
#define NROUND2 128 * 8

/*no-optimized date update function*/
void state_update_struc(unsigned int *state, const unsigned int *key, unsigned int number_of_steps)
{
  unsigned int i;
  unsigned int t1, t2, t3, t4, feedback;
  for (i = 0; i < (number_of_steps >> 5); i++)
  {
    t1 = (state[1] >> 15) | (state[2] << 17); // 47 = 1*32+15
    t2 = (state[2] >> 6)  | (state[3] << 26);  // 47 + 23 = 70 = 2*32 + 6
    t3 = (state[2] >> 21) | (state[3] << 11); // 47 + 23 + 15 = 85 = 2*32 + 21
    t4 = (state[2] >> 27) | (state[3] << 5);  // 47 + 23 + 15 + 6 = 91 = 2*32 + 27
    feedback = state[0] ^ t1 ^ (~(t2 & t3)) ^ t4 ^ key[i & 3];
    // shift 32 bit positions
    state[0] = state[1];
    state[1] = state[2];
    state[2] = state[3];
    state[3] = feedback;
  }
}

// The initialization
/* The input to initialization is the 128-bit key; 96-bit IV;*/
void initialization_struc(const unsigned int *key, const unsigned int *iv, unsigned int *state)
{
  unsigned int i;
  
  // initialize the state as 0
  for (i = 0; i < 4; i++)
    state[i] = 0;

  // update the state with the key
  state_update_struc(state, key, NROUND2);

  // introduce IV into the state
  for (i = 0; i < 3; i++)
  {
    state[1] ^= FrameBitsIV;
    state_update_struc(state, key, NROUND1);
    state[3] ^= iv[i];
  }
}

// process the associated data
void process_ad_struc(const unsigned int *k, const unsigned int *ad,
                      unsigned int adlen, unsigned int *state)
{
  unsigned int i;

  for (i = 0; i < (adlen >> 2); i++)
  {
    state[1] ^= FrameBitsAD;
    state_update_struc(state, k, NROUND1);
    state[3] ^= ad[i];
  }
}

// encrypt plaintext
int crypto_aead_encrypt_struc(
    unsigned int *c,
    const unsigned int *m,
    const unsigned int *ad,
    const unsigned int *npub,
    const unsigned int *k)
{
  unsigned int mlen = 16;
  unsigned int adlen = 16;

  unsigned int i;
  unsigned int j;
  unsigned int mac[8];
  unsigned int state[4];

  // initialization stage
  initialization_struc(k, npub, state);

  // process the associated data
  process_ad_struc(k, ad, adlen, state);

  // process the plaintext
  for (i = 0; i < (mlen >> 2); i++)
  {
    state[1] ^= FrameBitsPC;
    state_update_struc(state, k, NROUND2);
    state[3] ^= m[i];
    c[i] = state[2] ^ m[i];
  }


  // finalization stage, we assume that the tag length is 8 bytes
  state[1] ^= FrameBitsFinalization;
  state_update_struc(state, k, NROUND2);
  mac[0] = state[2];

  state[1] ^= FrameBitsFinalization;
  state_update_struc(state, k, NROUND1);
  mac[1] = state[2];

  for (j = 0; j < 2; j++)
    c[(mlen>>2) + j] = mac[j];
  return 0;
}

// decrypt a message
int crypto_aead_decrypt_struc(
    unsigned int *m,
    const unsigned int *c,
    const unsigned int *ad,
    const unsigned int *npub,
    const unsigned int *k)
{
  unsigned int mlen = 16;
  unsigned int adlen = 16;
  unsigned int clen = mlen + 8;

  unsigned int i;
  unsigned int j, check = 0;
  unsigned int mac[8];
  unsigned int state[4];

  // initialization stage
  initialization_struc(k, npub, state);

  // process the associated data
  process_ad_struc(k, ad, adlen, state);

  // process the ciphertext
  for (i = 0; i < (mlen >> 2); i++)
  {
    state[1] ^= FrameBitsPC;
    state_update_struc(state, k, NROUND2);
    m[i] = state[2] ^ c[i];
    state[3] ^= m[i];
  }

  // finalization stage, we assume that the tag length is 8 bytes
  state[1] ^= FrameBitsFinalization;
  state_update_struc(state, k, NROUND2);
  mac[0] = state[2];

  state[1] ^= FrameBitsFinalization;
  state_update_struc(state, k, NROUND1);
  mac[1] = state[2];

  // verification of the authentication tag
  for (j = 0; j < 2; j++)
  {
    check |= (mac[j] ^ c[(clen>>2) - 2 + j]);
  }
  return check;
}
