unsigned int findmax_naive(const unsigned int *array)
{

  unsigned int n = 1000;
  unsigned int i, m, c;

  m = array[0];
  for(i=1; i<n; i++){
    c = m < array[i];
    m = c ? array[i] : m;
  }
  unsigned int max = m;
  return max;
}
