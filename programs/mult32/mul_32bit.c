#define HI(x) (x >> 16)
#define LO(x) (x & 0xFFFF)

// 32-bit multiplication
// (z[0], z[1]) = x * y 
unsigned int msb32_from_mul(const unsigned int x, const unsigned int y) {
    unsigned int z1, z2, z3;     
    unsigned int t = LO(x) * LO(y);
    t = HI(x) * LO(y) + HI(t);
    z1 = LO(t);
    z2 = HI(t);
    t = z1 + LO(x) * HI(y);
    t = z2 + HI(x) * HI(y) + HI(t);
    z2 = LO(t);
    z3 = HI(t);
    return z3 << 16 | z2;
}