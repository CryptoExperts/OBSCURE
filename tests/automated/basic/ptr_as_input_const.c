unsigned int f(unsigned int x, const unsigned int* p, unsigned int y) {
  unsigned int a = x * p[0];
  unsigned int b = y * p[2];
  unsigned int c = a & p[4];
  return b ^ c;
}
