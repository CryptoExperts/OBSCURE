unsigned int f(const unsigned int arr[6]) {
  unsigned int* p = &arr[2];
  unsigned int* q = &arr[4];
  return arr[0] ^ arr[1] ^ p[0] ^ p[3] ^ q[0] ^ arr[3];
}
