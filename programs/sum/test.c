#include <stdlib.h>
#include <time.h>
#include <stdio.h>

#define N_TEST    5
#define ARRAY_LEN 1000 // Fixed array size

unsigned int sum_naive(const unsigned int *array);
unsigned int sum_tree(const unsigned int *array);

int main()
{
  srand(time(NULL));
  for (int t=0; t<N_TEST; t++){
    unsigned int s_naive, s_tree;
    unsigned int array[ARRAY_LEN];
    unsigned int i;
    for (i=0; i<ARRAY_LEN; i++) array[i] = rand();
    s_naive = sum_naive(array);
    s_tree = sum_tree(array);
    if (s_naive == s_tree){
      printf("OK! s (naive) = s (tree) = %u\n", s_naive);
    }
    else {
      printf("Error!\n");
      printf("s (naive) = %u\n", s_naive);
      printf("s (tree)  = %u\n", s_tree);
    }
  }
}