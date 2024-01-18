CC = cc
CFLAGS = -O3 -Wall -Wextra

all: test

test: test.o ascon128v12_orig.o permutations.o ascon128v12_struc.o
	$(CC) $(CFLAGS) $^ -o $@

ascon128v12_orig.o: ascon128v12_orig.c \
					api.h ascon.h word.h \
					permutations.h printstate.h \
					endian.h forceinline.h interleave.h
	$(CC) $(CFLAGS) -c $< -o $@

permutations.o: permutations.c \
				permutations.h api.h ascon.h \
				config.h round.h printstate.h
	$(CC) $(CFLAGS) -c $< -o $@

%.o : %.c
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: clean

clean:
	rm *.o test