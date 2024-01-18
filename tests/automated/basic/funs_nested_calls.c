unsigned int h(unsigned int x, unsigned int y) {
  return x + y;
}

unsigned int g(unsigned int x, unsigned int y) {
  return h(x, y);
}

unsigned int f(unsigned int a, unsigned int b) {
  unsigned int m = g(a, b);
  unsigned int n = g(a, b);
  return m + n;
}
