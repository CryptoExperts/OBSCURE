unsigned int f(unsigned int x, unsigned int y) {
  unsigned int arr[2] = { x, y };
  unsigned int* ptr = arr;
  ptr[1] = ptr[1] + 11223483;
  ptr[0] = ptr[0] + 9889374;
  return ptr[0] * ptr[1];
}
