unsigned int f(unsigned int arr[4]) {
  arr[0] ^= arr[3];
  arr[1] ^= arr[2];
  return arr[0] + arr[1] + arr[2] + arr[3];
}
