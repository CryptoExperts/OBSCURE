unsigned int g(unsigned int x, unsigned int y) {
  return x + y;
}

unsigned int f(unsigned int a, unsigned int b) {
  unsigned int m;
  m = a + g(a, b);
  return m;
}
