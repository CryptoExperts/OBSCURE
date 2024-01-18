unsigned int f(unsigned int x) {
  unsigned int arr[3];
  arr[0] = x | 12398243;
  arr[1] = arr[0] + 5679234;
  arr[2] = arr[1] * arr[0];
  return arr[2];
}
