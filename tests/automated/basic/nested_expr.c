unsigned int f(unsigned int a, unsigned int b) {
  unsigned int x = a + b * a;
  unsigned int y = (++x + a++) << 2;
  unsigned int z = x * y + (++b - y) ^ x;
  return (z >> 1) + a * ((b - x++) ^ y);
}
