// --- Testing mnist

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long u64;

#include <stdio.h>        // just for printf
#include "mnist_dataset.h" // import the test dataset (flattened 28x28 grayscale images cast to u32)

u8 mnist32(u32 *x0);
u32 mnist32_struc(u32 *x0);


int main()
{
  u16 i, errors_mnist = 0, errors_mnist_struc = 0;

  for (i = 0; i < 10000; i++)
    errors_mnist += (mnist32(X[i]) == Y[i]) ? 0 : 1;

  for (i = 0; i < 10000; i++)
    errors_mnist_struc += (mnist32_struc(X[i]) == Y[i]) ? 0 : 1;

  if (errors_mnist != errors_mnist_struc){
    printf("Restructure failed!");
    printf("Original mnist    : %d / 10000 classification errors, accuracy of %.2f%%\n",
            errors_mnist,
            100 - (float)errors_mnist / 100);
    printf("Restructured mnist: %d / 10000 classification errors, accuracy of %.2f%%\n",
            errors_mnist_struc,
            100 - (float)errors_mnist_struc / 100);
  }
  else {
    printf("OK\n");
  }

  return 0;
}

// --- done.