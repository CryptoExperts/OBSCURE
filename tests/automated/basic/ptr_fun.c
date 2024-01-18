unsigned int g(unsigned int* a) {
  a[0] += a[1];
  a[2] += a[3];
  return a[0] * a[2];
}

unsigned int h(unsigned int* arr) {
  return g(arr);
}

unsigned int f(unsigned int w, unsigned int x,
               unsigned int y, unsigned int z) {
  unsigned int arr[4] = { w, x, y, z };
  unsigned int *p = arr;
  unsigned int a = h(p);
  a += p[0];
  a &= p[1];
  a |= p[2];
  a ^= p[3];
  return a;
}
