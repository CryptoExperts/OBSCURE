unsigned int f(unsigned int a, unsigned int b, unsigned int c) {
  unsigned int k = a + b;
  unsigned int l = 42;
  unsigned int m = c + l;
  unsigned int o = l + m;
  unsigned int e = m + o;
  l = l | k;
  o = e & m;
  o = o - a;
  o = o ^ c;
  m = l ^ o;
  o = m << 4;
  a = m * m;
  return a + o;
}
