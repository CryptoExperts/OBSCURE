unsigned int times3(unsigned int x) {
  return x * 3;
}

unsigned int g(unsigned int x, unsigned int y) {
  unsigned int a = x + 42;
  unsigned int b = y + 127;
  return a * b;
}

unsigned int f(unsigned int x, unsigned int y, unsigned int z) {
  unsigned int a = g(x, y);
  unsigned int b = times3(a);
  unsigned int c = times3(b);
  unsigned int d = g(b, c);
  return d * z;
}

unsigned int h(unsigned int x, unsigned int y) {
  return f(x, y, y);
}
