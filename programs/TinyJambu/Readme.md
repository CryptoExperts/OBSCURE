TinyJambu
====

This folder contains 2 implementations of TinyJambu
(`tinyjambu128v2_*`), as well as a main (`test.c`) to check if both
those implementations seem functionally equivalent
(experimentally). Those 2 implementations are:

 - `tinyjambu128v2_orig.c`: the reference implementation, taken from
   the NIST submission
 
 - `tinyjambu128v2_struc.c`: the reference implementation simplified a
   bit, so that our compiler can compile it.



## Differences between the 2 version

To obtain the `struct` from the `orig` version, we did the following
modifications:
 - removed two "if" (whose condition depended on adlen and mlen)
 - removed clen parameter
 - fixed mlen to 16 (and removed param)
 - fixed adlen to 16 (and removed param adlen)
 - change type of pointers to "unsigned int*" instead of "unsigned char*"
    + removed "unsigned int*" casts
    + changed number of iterations of final loop to 2 instead of 8,
      and used (mlen >> 2) instead of mlen in this loop
      (for (j = 0; j < 2; j++) c[(mlen>>2)+j] = mac[j];)
      because "c" and "mac" are now "unsigned int*" instead of "unsigned char*"
 - changed all scalar types to "unsigned int"
 - removed unused parameter nsec


## Compiling/obfuscating the _struc.c version

To generate a code that can be compiled from `tinyjambu128v2_struc.c`,
you'll need to:

 - remove either `crypto_aead_encrypt_struc` or `crypto_aead_decrypt_struc`
 - run `cpp -P tinyjambu128v2_struc.c -o TinyJambu.c` in order to
   remove comments and `#define`s


## Testing that both versions are (seemingly) equivalent

Simply run:

    make
    ./test
