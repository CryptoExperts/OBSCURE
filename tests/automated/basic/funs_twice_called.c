unsigned int f(unsigned int x) {
  return x;
}

unsigned int g(unsigned int a, unsigned int b) {
  a = f(a);
  b = f(b);
  return a ^ b;
}
