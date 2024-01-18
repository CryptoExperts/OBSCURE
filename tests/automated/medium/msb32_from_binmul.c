unsigned int msb32_from_binmul(const unsigned int x, const unsigned int y)
{
  unsigned int t[32];
  unsigned int i, j, b, mask;
  for (i = 0; i < 32; i++)
  {
    mask = 1 << i;
    b = (y & mask) >> i;
    t[i] = b ? x : 0;
  }

  unsigned int z0 = 0;
  unsigned int z1 = 0;
  unsigned int zb, zi;
  unsigned int r = 0;

  for (i = 0; i < 32; i++)
  {
    zb = 0;
    for (j = 0; j <= i; j++)
    {
      mask = 1 << (i - j);
      b = (mask & t[j]) >> (i - j);
      zb = zb + b;
    }
    zb = zb + r;
    zi = zb % 2;
    r = zb / 2;

    zi = zi << i;
    z1 = z1 | zi;
  }

  for (i = 31; i > 0; i--)
  {
    zb = 0;
    for (j = 32 - i; j < 32; j++)
    {
      mask = 1 << ((32 - j) + (31 - i));
      b = (mask & t[j]) >> ((32 - j) + (31 - i));
      zb = zb + b;
    }
    zb = zb + r;
    zi = zb % 2;
    r = zb / 2;
    zi = zi << (31 - i);
    z0 = z0 | zi;
  }

  zi = r;
  zi = zi << 31;
  z0 = z0 | zi;

  return z0;
}
