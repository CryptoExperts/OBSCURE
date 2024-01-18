unsigned int f(unsigned int x, unsigned int y) {
  unsigned int arr[2] = { x, y };
  unsigned int* p;
  arr[0] ^= arr[1];
  p = arr;
  p[0] += p[1];
  p[1] *= p[0];
  return p[1] + p[0];
}
