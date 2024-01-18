unsigned int f(unsigned int w, unsigned int x,
               unsigned int y, unsigned int z) {
  unsigned int arr[4] = { w, x, y, z };
  unsigned int *p = arr;
  p[0] ^= p[1];
  unsigned int* q = p;
  q[1] ^= q[2];
  unsigned int* r = arr;
  r[2] ^= r[3];
  r[0] += p[1];
  q[3] -= r[2];
  arr[1] ^= p[3];
  unsigned int check = q[0] ^ r[1];
  check ^= p[2];
  check ^= arr[3];
  return check;
}
