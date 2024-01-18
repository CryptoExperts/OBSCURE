unsigned int f(unsigned int a, unsigned int b) {
  unsigned int expected_result = 47;
  a = a + 19;
  b = b * 4;
  unsigned int t = a | 14;
  for (unsigned int i = 0; i < 4; i++) {
    t = t + b;
  }
  unsigned int bound = 16;
  for (b = 14; b < bound; ++b)
    for (unsigned int c = 8; c > b; c++)
      t = t * a;
  return t;
}
