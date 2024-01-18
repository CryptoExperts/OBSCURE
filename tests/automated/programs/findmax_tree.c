unsigned int findmax_tree(const unsigned int *array)
{


  unsigned int n = 1000;
  unsigned int i, c, cl;
  unsigned int m = (n+1)/2;
  unsigned int tmp[500];
  unsigned int last1 = array[n-1];
  unsigned int last2 = array[n-2];
  unsigned int mlast;

  for(i=0; i<m-1; i++){
    c = array[2*i] < array[2*i+1];
    tmp[i] = c ? array[2*i+1] : array[2*i];
  }



  cl = n % 2;
  c = last2 < last1;
  mlast = c ? last1 : last2;
  tmp[m-1] = cl ? last1 : mlast;

  last1 = tmp[m-1];
  last2 = tmp[m-2];
  c = last2 < last1;
  mlast = c ? last1 : last2;
  cl = m % 2;

  for(m=(m+1)/2; m>1; m=(m+1)/2){
    for(i=0; i<m-1; i++){
      c = tmp[2*i] < tmp[2*i+1];
      tmp[i] = c ? tmp[2*i+1] : tmp[2*i];
    }
    tmp[m-1] = cl ? last1 : mlast;

    last1 = tmp[m-1];
    last2 = tmp[m-2];
    c = last2 < last1;
    mlast = c ? last1 : last2;
    cl = m % 2;
  }

  c = tmp[0] < tmp[1];
  unsigned int max = c ? tmp[1] : tmp[0];
  return max;
}
