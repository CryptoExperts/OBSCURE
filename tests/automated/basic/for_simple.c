unsigned int f(unsigned int a, unsigned int b) {
  unsigned int expected_result = 1069874943;
  a = a + 19;
  b = b * 4;
  unsigned int t = a | 14;
  for (unsigned int i = 0; i < 4; i++) {
    t = t + b;
  }
  for (b = 14; b < 16; ++b)
    for (unsigned int c = 8; c > 2; c--)
      t = t * a;
  return t;
}
