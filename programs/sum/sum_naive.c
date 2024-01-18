unsigned int sum_naive(const unsigned int *array)
{
  // fix the size of array
  unsigned int n = 1000;
  unsigned int i;
  unsigned int s = 0;
  for (i=0; i<n; i++){
    s += array[i];
  }
  return s;
}