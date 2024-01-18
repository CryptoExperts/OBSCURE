unsigned int f(unsigned int x, unsigned int y) {
  unsigned int arr[4];
  arr[0] = x;
  for (unsigned int i = 0; i < 3; i++) {
    arr[i+1] = arr[i] * y;
    arr[i+1] += arr[i];
  }
  unsigned int check = arr[0] ^ arr[1];
  check ^= arr[2];
  check ^= arr[3];
  return check;
}
