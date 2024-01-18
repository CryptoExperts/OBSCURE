unsigned int sum_tree(const unsigned int *array)
{
  // Fix the size of array
  // This algo works with n > 2
  unsigned int n = 1000;
  unsigned int i;
  unsigned int m = (n+1)/2;
  unsigned int tmp[500]; // tmp[m]
  unsigned int last1 = array[n-1];
  unsigned int last2 = array[n-2];
  unsigned int cond;

  for (i=0; i<m-1; i++){
    tmp[i] = array[2*i] + array[2*i+1];
  }

  // If n is odd, then copy the last element
  // Else compute the sum of the last 2 elements
  cond = n % 2;
  tmp[m-1] = cond * last1 + (1-cond) * (last1 + last2);

  last1 = tmp[m-1];
  last2 = tmp[m-2];
  cond = m % 2;

  for (m=(m+1)/2; m>1; m=(m+1)/2){
    for (i=0; i<m-1; i++){
      tmp[i] = tmp[2*i] + tmp[2*i+1];
    }
    tmp[m-1] = cond * last1 + (1-cond) * (last1 + last2);

    cond = m % 2;
    last1 = tmp[m-1];
    last2 = tmp[m-2];
  }

  unsigned int s = tmp[0] + tmp[1];
  return s;
}