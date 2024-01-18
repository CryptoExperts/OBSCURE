// --- 32-bit neural net that classifies handwritten digits (MNIST use case)

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long u64;

#include "mnist_weights.h"   // integer weights (small signed integers cast to u32)
#include "mnist_biases.h"    // biases (cast to u32)
#include "mnist_encodings.h" // encoding parameters (cast to u32)

u32 activation(u8 layer, u16 i, u32 y)
{
  if (y < THRESHOLD[layer][i])
    return 0;

  u32 diff = y - THRESHOLD[layer][i];
  u64 product = (u64)SLOPE[layer] * diff;
  u32 quotient = (u32)(product >> 32);
  return quotient;
}

u8 mnist32(u32 *x0)
// MNIST classification of a flattened u32 28x28 image, returns a class within [0-9]
{
  u32 x1[100], x2[100], x3[100], x4[100];
  u32 y, max = 0;
  u16 i, j;
  u8 pos = 0;

  for (i = 0; i < 100; i++) // layer 1: dense + activation
  {
    y = BIASES_1[i];
    for (j = 0; j < 784; j++)
      y += WEIGHTS_1[i][j] * x0[j];
    x1[i] = activation(0, i, y);
  }

  for (i = 0; i < 100; i++) // layer 2: dense + activation
  {
    y = BIASES_2[i];
    for (j = 0; j < 100; j++)
      y += WEIGHTS_2[i][j] * x1[j];
    x2[i] = activation(1, i, y);
  }

  for (i = 0; i < 100; i++) // layer 3: dense + activation
  {
    y = BIASES_3[i];
    for (j = 0; j < 100; j++)
      y += WEIGHTS_3[i][j] * x2[j];
    x3[i] = activation(2, i, y);
  }

  for (i = 0; i < 100; i++) // layer 4: dense + activation
  {
    y = BIASES_4[i];
    for (j = 0; j < 100; j++)
      y += WEIGHTS_4[i][j] * x3[j];
    x4[i] = activation(3, i, y);
  }

  for (i = 0; i < 10; i++) // layer 5: dense + find arg max in [0-9]
  {
    y = BIASES_5[i];
    for (j = 0; j < 100; j++)
      y += WEIGHTS_5[i][j] * x4[j];
    if (y > max)
    {
      max = y;
      pos = i;
    }
  }

  return pos;
}
