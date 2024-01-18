unsigned int f(unsigned int x) {
  unsigned int arr[4] = { x, 123432, 123344 };
  unsigned int a = arr[0] + arr[1];
  unsigned int b = arr[2] + arr[3];
  return a * b;
}
