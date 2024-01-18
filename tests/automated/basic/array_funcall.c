unsigned int f(unsigned int a, unsigned int b) {
  return a + b;
}

unsigned int g(unsigned int x, unsigned int y) {
  unsigned int arr[2];
  arr[0] = f(x, y);
  return arr[0];
}
