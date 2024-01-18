CC = cc
CFLAGS = -O3 -Wall -Wextra

all: test

test: test.o findmax_naive.o findmax_tree.o
	$(CC) $(CFLAGS) $^ -o $@

%.o : %.c
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: clean

clean:
	rm *.o