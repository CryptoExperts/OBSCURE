CC = cc
CFLAGS = -O3 -Wall -Wextra

all: test

test: test.o mul_32bit.o mulbin_32bit.o
	$(CC) $(CFLAGS) $^ -o $@

%.o : %.c
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: clean

clean:
	rm *.o