unsigned int f(unsigned int a, unsigned int b) {
  unsigned int expected_result = 2083191999;
  a = a + 19;
  b = b * 4;
  unsigned int one = 1;
  unsigned int t = a | 14;
  for (unsigned int i = 1; i < 4; i *= 2) {
    t = t + b;
  }
  unsigned int bound = 20;
  for (b = 14; b < bound; b = b + (one << 1))
    for (unsigned int c = 22; c > b; --c)
      t = t * a;
  return t;
}
