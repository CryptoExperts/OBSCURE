unsigned int f(unsigned int x) {
  unsigned int a = 0;
  a += 42;
  a ^= x;
  unsigned int b = a + 2;
  return b;
}
