#include <stdlib.h>
#include <time.h>
#include <stdio.h>

#define N_TEST    5
#define ARRAY_LEN 1000 // Fixed array size

unsigned int findmax_naive(unsigned int *array);
unsigned int findmax_tree(unsigned int *array);

int main()
{
  srand(time(NULL));
  for (int t=0; t<N_TEST; t++){
    unsigned int m_naive, m_tree;
    unsigned int array[ARRAY_LEN];
    unsigned int i;
    for (i=0; i<ARRAY_LEN; i++) array[i] = rand();
    m_naive = findmax_naive(array);
    m_tree = findmax_tree(array);

    if (m_naive == m_tree){
      printf("OK! max (naive) = max (tree) = %u\n", m_naive);
    }
    else {
      printf("Error!\n");
      printf("max (naive) = %u\n", m_naive);
      printf("max (tree)  = %u\n", m_tree);
    }
  }
}