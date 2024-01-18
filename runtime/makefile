CC = cc
LIBS = -lsodium -lm
CFLAGS = -O3 -Wall -Wextra


SCHWAEMM_DIR = sparkle/schwaemm
ESCH_DIR = sparkle/esch

all: interpreter

interpreter: main.o interpreter.o SEalgo.o hash.o aead.o utils.o
	$(CC) $(CFLAGS) $^ hash_ref.o aead_ref.o $(LIBS) -o $@

interpreter.o: interpreter.c interpreter.h SEconfig.h crypto_uint.h crypto_len.h program.h multi_instruction.h
	$(CC) $(CFLAGS) -c $< -o $@

SEalgo.o: SEalgo.c SEalgo.h crypto_uint.h crypto_len.h multi_instruction.h SEconfig.h
	$(CC) $(CFLAGS) -c $< -o $@

aead.o: $(SCHWAEMM_DIR)/*.h $(SCHWAEMM_DIR)/*.c
	$(CC) $(CFLAGS) -c $(SCHWAEMM_DIR)/schwaemm.c -o aead.o
	$(CC) $(CFLAGS) -c $(SCHWAEMM_DIR)/sparkle.c -o aead_ref.o

hash.o: $(ESCH_DIR)/*.h $(ESCH_DIR)/*.c
	$(CC) $(CFLAGS) -c $(ESCH_DIR)/esch.c -o hash.o
	$(CC) $(CFLAGS) -c $(ESCH_DIR)/sparkle.c -o hash_ref.o

utils.o: utils.c utils.h SEconfig.h crypto_uint.h
%.o : %.c %.h $(GLOBAL_HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: clean

clean:
	rm *.o interpreter
