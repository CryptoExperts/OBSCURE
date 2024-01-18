unsigned int f(unsigned int x, const unsigned int* p_in, unsigned int* p_out, unsigned int y) {
  p_out[0] = x * p_in[0];
  p_out[1] = y * p_in[2];
  p_out[2] = p_out[0] & p_in[4];
  return p_out[0] ^ p_out[1] ^ p_out[2];
}
