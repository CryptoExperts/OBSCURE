unsigned int f(unsigned int a, unsigned int b,unsigned int c){
  unsigned int x = (a % 2 ? b % 3 : c % 4) ? (c & 1 ? a + c : b + c) : b + c;
  return x % 2 ? x : a % 2 ? x : x + 1;
}
