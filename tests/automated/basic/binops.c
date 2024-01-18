unsigned int f(unsigned int a, unsigned int b, unsigned int c) {
  unsigned int expected = 451586;
  unsigned int k = a + b;
  unsigned int l = 42;
  unsigned int m = c + l;
  unsigned int o = l + m;
  unsigned int d = 12, e = m + o;
  l = l | k;
  o = o & c;
  o = o - a;
  m = l ^ b;
  m = m << 4;
  m = m;
  a = m * m;
  return a + o;
}
