#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

unsigned int msb32_from_mul(const unsigned int x, const unsigned int y);
unsigned int msb32_from_binmul(const unsigned int x, const unsigned int y);

#define N_TEST = 1000

typedef unsigned long long u64;
typedef unsigned int u32;

int main()
{
  srand(time(NULL));
  u32 x = rand();
  u32 y = rand();
  u32 z = (((u64) x) * ((u64) y)) >> 32;

  u32 z1 = msb32_from_binmul(x, y);
  u32 z2 = msb32_from_mul(x, y);

  if ((z != z1) || (z != z2)){
    printf("Error: \n");
    printf("%u \n", z);
    printf("%u \n", z1);
    printf("%u \n", z2);
  }
  else{
    printf("OK\n");
  }
  return 0;
}