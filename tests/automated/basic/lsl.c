unsigned int f(unsigned int a, unsigned int b, unsigned int c){
    unsigned int x = a << b;
    x = x << 1;
    x = x << c;
    return x;
}