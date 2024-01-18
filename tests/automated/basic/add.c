unsigned int f(unsigned int a, unsigned int b){
    unsigned int x = a + b;
    x = x + a;
    x = x + b;
    return x;
}