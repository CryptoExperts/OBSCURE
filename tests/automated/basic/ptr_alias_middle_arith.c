void g(unsigned int r[2], const unsigned int x[2]){
	r[0] = x[0] + 99;
	r[1] = x[1] + 88;
}

unsigned int f(unsigned int r[8], const unsigned int x[8]){
	unsigned int i;
  unsigned int *a, *b;
	for(i = 0; i < 4; i++){
    a = r + i*2;
    b = r + i*2;
		g(a, b);
	}
	return 0;
}
