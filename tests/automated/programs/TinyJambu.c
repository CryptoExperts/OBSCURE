void state_update_struc(unsigned int *state, const unsigned int *key, unsigned int number_of_steps)
{
  unsigned int i;
  unsigned int t1, t2, t3, t4, feedback;
  for (i = 0; i < (number_of_steps >> 5); i++)
  {
    t1 = (state[1] >> 15) | (state[2] << 17);
    t2 = (state[2] >> 6) | (state[3] << 26);
    t3 = (state[2] >> 21) | (state[3] << 11);
    t4 = (state[2] >> 27) | (state[3] << 5);
    feedback = state[0] ^ t1 ^ (~(t2 & t3)) ^ t4 ^ key[i & 3];
    state[0] = state[1];
    state[1] = state[2];
    state[2] = state[3];
    state[3] = feedback;
  }
}
void initialization_struc(const unsigned int *key, const unsigned int *iv, unsigned int *state)
{
  unsigned int i;
  for (i = 0; i < 4; i++)
    state[i] = 0;
  state_update_struc(state, key, 128 * 8);
  for (i = 0; i < 3; i++)
  {
    state[1] ^= 0x10;
    state_update_struc(state, key, 128 * 5);
    state[3] ^= iv[i];
  }
}
void process_ad_struc(const unsigned int *k, const unsigned int *ad,
                      unsigned int adlen, unsigned int *state)
{
  unsigned int i;
  for (i = 0; i < (adlen >> 2); i++)
  {
    state[1] ^= 0x30;
    state_update_struc(state, k, 128 * 5);
    state[3] ^= ad[i];
  }
}
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
  initialization_struc(k, npub, state);
  process_ad_struc(k, ad, adlen, state);
  for (i = 0; i < (mlen >> 2); i++)
  {
    state[1] ^= 0x50;
    state_update_struc(state, k, 128 * 8);
    state[3] ^= m[i];
    c[i] = state[2] ^ m[i];
  }
  state[1] ^= 0x70;
  state_update_struc(state, k, 128 * 8);
  mac[0] = state[2];
  state[1] ^= 0x70;
  state_update_struc(state, k, 128 * 5);
  mac[1] = state[2];
  for (j = 0; j < 2; j++)
    c[(mlen>>2) + j] = mac[j];
  return 0;
}
