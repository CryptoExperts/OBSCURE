unsigned int f(unsigned int x) {
  unsigned int a = 0xff;
  unsigned int b = a + 0x1324;
  unsigned int c = 0x1233323 + b;
  return x * c;
}
