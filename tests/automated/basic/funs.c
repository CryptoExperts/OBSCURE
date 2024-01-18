unsigned int f(unsigned int a) {
  return a * 3;
}

unsigned int h(unsigned int x) {
  x = x + 1;
  return f(x);
}
