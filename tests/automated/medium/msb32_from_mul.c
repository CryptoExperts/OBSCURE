unsigned int msb32_from_mul(const unsigned int x, const unsigned int y) {
    unsigned int z1, z2, z3;
    unsigned int t = (x & 0xFFFF) * (y & 0xFFFF);
    t = (x >> 16) * (y & 0xFFFF) + (t >> 16);
    z1 = (t & 0xFFFF);
    z2 = (t >> 16);
    t = z1 + (x & 0xFFFF) * (y >> 16);
    t = z2 + (x >> 16) * (y >> 16) + (t >> 16);
    z2 = (t & 0xFFFF);
    z3 = (t >> 16);
    return z3 << 16 | z2;
}
