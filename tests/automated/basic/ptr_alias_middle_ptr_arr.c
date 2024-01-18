unsigned int f(const unsigned int* arr) {
  unsigned int* p = arr + 2;
  unsigned int* q = &p[2];
  return arr[0] ^ arr[1] ^ p[0] ^ p[3] ^ q[0] ^ arr[3];
}
