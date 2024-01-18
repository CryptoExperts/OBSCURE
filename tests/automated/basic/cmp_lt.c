unsigned int f(unsigned int a, unsigned int b){
    unsigned int c;
    unsigned int d;
    unsigned int e;
    unsigned int f;
    unsigned int g;
    unsigned int x;
    c = a < b;
    d = 5 < 3;
    e = 3 < 5;
    f = a < 5;
    g = c | d | e | f;
    x = g ? a : b;
    return x;
}