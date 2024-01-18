void swap(unsigned int x[2],
          const unsigned int y[2]) {
  x[0] = y[1];
  x[1] = y[0];
}

unsigned int f(const unsigned int out[2],
               const unsigned int in[2]) {
  unsigned int x[2];
  swap(x, in);
  return 0;
}
