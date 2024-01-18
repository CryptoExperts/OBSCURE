Ascon32
====

This folder contains 2 implementations of Ascon
(`ascon128v12_*`), as well as a main (`test.c`) to check if both
those implementations seem functionally equivalent
(experimentally). Those 2 implementations are:

 - `ascon128v12_orig.c`: the reference implementation, taken from
   the NIST submission (Implementations/crypto_aead/ascon128v12/bi32)

 - `ascon128v12_struc.c`: the reference implementation simplified a
   bit, so that our compiler can compile it.



## Differences between the 2 version

To obtain the `struct` from the `orig` version, we did the following
modifications:
 - removed the structure `state_t` and `word_t`. Used an array containing 10 elements instead (`unsigned int s[10]`). In this array, `s[0]` and `s[1]` represent `x0` of a word in the original version, where `s[0] = x0.o` and `s[1] = x0.e`. Similarly, we have:
    + `s[2] = x1.o`, `s[3] = x1.e`
    + `s[4] = x2.o`, `s[5] = x2.e`
    + `s[6] = x3.o`, `s[7] = x3.e`
    + `s[8] = x4.o`, `s[9] = x4.e`
 - replaced ternary operations (`v = condition ? X : Y`) by `v = c*X + (1-c)*Y`, where `c` is 0 or 1.
 - replaced pass-by-address in function calls with pass-by-pointer.
 - removed `if` (whose condition depended on `adlen` and `mlen`).
 - removed parameters `clen`, `mlen`, `adlen` and `nsec` (unused) in the prototypes.
 - fixed `mlen` and `adlen` to 16 in the function.
 - replaced functions related to `uint64_t` with functions working on `unsigned int`
 - change type of pointers to `unsigned int*` instead of `unsigned char*`
    + removed conversion functions from `unsigned char *` to `unsigned int *` and vice versa.
    + replaced `while` by `for` and changed the number of iterations.
 - changed all scalar types to `unsigned int`.
 - removed all casts of numbers to `uint64_t`.
 - removed macro `forceinline`.


## Compiling/obfuscating the _struc.c version

To generate a code that can be compiled from `ascon128v12_struc.c`,
you'll need to:

 - remove either `crypto_aead_encrypt_struc` or `crypto_aead_decrypt_struc`
 - run `cpp -P ascon128v12_struc.c -o Ascon.c` in order to
   remove comments and `#define`s


## Testing that both versions are (seemingly) equivalent

Simply run:

    make
    ./test
