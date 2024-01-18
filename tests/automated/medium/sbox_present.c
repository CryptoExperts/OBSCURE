void sbox(const unsigned int in[4], unsigned int out[4]) {
  unsigned int T1 = in[1] ^ in[2];
  unsigned int T2 = in[2] & T1;
  unsigned int T3 = in[3] ^ T2;
  out[0] = in[0] ^ T3;
  unsigned int T4 = T1 & T3;
  unsigned int T5 = T1 ^ out[0];
  unsigned int T6 = T4 ^ in[2];
  unsigned int T7 = in[0] | T6;
  out[1] = T5 ^ T7;
  unsigned int T8 = T6 ^ ~in[0];
  out[3] = out[1] ^ T8;
  unsigned int T9 = T8 | T5;
  out[2] = T3 ^ T9;
}
