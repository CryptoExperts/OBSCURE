unsigned int f(unsigned int a, unsigned int b){
  a &= b;
  a |= 123456788;
  a ^= b;
  a += b;
  a *= b;
  a >>= 6;
  a <<= 10;
  b %= 234;
  a /= b;
  a *= 29;
  a -= b;
  return a;
}
