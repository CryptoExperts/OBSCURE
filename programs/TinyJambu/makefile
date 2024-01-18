CC = cc
CFLAGS = -O3 -Wall -Wextra

all: test

test: test.o tinyjambu128v2_orig.o tinyjambu128v2_struc.o
	$(CC) $(CFLAGS) $^ -o $@

%.o : %.c
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: clean

clean:
	rm *.o