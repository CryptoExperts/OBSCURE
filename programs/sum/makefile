CC = cc
CFLAGS = -O3 -Wall -Wextra

all: test

test: test.o sum_naive.o sum_tree.o
	$(CC) $(CFLAGS) $^ -o $@

%.o : %.c
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: clean

clean:
	rm *.o