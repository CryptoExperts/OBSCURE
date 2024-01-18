CFLAGS = -O3 -Wall -Wextra

all: test

test: test.o tracingAES.o key_sched.o
	$(CC) $(CFLAGS) $^ -o $@

%.o : %.c
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: clean

clean:
	rm *.o