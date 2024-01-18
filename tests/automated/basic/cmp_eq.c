unsigned int f(unsigned int a, unsigned int b){
    unsigned int c;
    unsigned int d;
    unsigned int e;
    unsigned int f;
    unsigned int g;
    unsigned int x;
    c = (a == b);
    d = (5 == 5);
    e = (a == 5);
    f = (5 == 3);
    g = c | d | e | f;
    x = g ? a : b;
    return x;
}