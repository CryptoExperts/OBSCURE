unsigned int f(unsigned int a, unsigned int b){
    unsigned int x = a & b;
    unsigned int y = x & 1;
    return y;
}