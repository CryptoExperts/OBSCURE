CFLAGS = -O3 -Wall -Wextra

all: test

test: test.o mnist.o mnist_struc.o
	$(CC) $(CFLAGS) $^ -o $@

%.o : %.c
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: clean

clean:
	rm *.o test