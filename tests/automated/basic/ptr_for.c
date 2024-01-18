unsigned int f(unsigned int x, unsigned int y) {
  unsigned int arr[4];
  unsigned int* p = arr;
  p[0] = x;
  for (unsigned int i = 0; i < 3; i++) {
    p[i+1] = p[i] * y;
    p[i+1] += p[i];
  }
  unsigned int check = p[0] ^ p[1];
  check ^= p[2];
  check ^= p[3];
  return check;
}
