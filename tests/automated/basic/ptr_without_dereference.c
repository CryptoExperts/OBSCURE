unsigned int f(unsigned int x, unsigned int y) {
  unsigned int arr[2] = { x, y };
  unsigned int* p;
  p = arr;
  unsigned int* q;
  q = p;
  return q[1] + q[0];
}
