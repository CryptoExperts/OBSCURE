unsigned int f(unsigned int x, unsigned int* p, unsigned int y) {
  p[0] = y;
  p[1] = x * 2;
  p[3] = p[0] + p[1];
  p[4] = p[2] & p[0];
  return p[3] ^ x;
}
