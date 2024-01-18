unsigned int g(unsigned int a[4]) {
  a[0] += a[1];
  a[2] += a[3];
  return a[0] * a[2];
}

unsigned int h(unsigned int arr[4]) {
  return g(arr);
}

unsigned int f(unsigned int w, unsigned int x,
               unsigned int y, unsigned int z) {
  unsigned int arr[4] = { w, x, y, z };
  unsigned int a = h(arr);
  a += arr[0];
  a &= arr[1];
  a |= arr[2];
  a ^= arr[3];
  return a;
}
