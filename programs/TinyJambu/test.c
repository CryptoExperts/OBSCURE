#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define KEY_LEN   16
#define NONCE_LEN 12
#define MAC_LEN   8
#define N_TEST    1000000

/********* Prototypes *********/
unsigned int crypto_aead_encrypt_struc(
	unsigned int *c,
	const unsigned int *m,
	const unsigned int *ad,
	const unsigned int *npub,
	const unsigned int *k
);

unsigned int crypto_aead_decrypt_struc(
	unsigned int *m,
	const unsigned int *c,
	const unsigned int *ad,
	const unsigned int *npub,
	const unsigned int *k
);

int crypto_aead_encrypt(
	unsigned char *c, unsigned long long *clen,
	const unsigned char *m, unsigned long long mlen,
	const unsigned char *ad, unsigned long long adlen,
	const unsigned char *nsec,
	const unsigned char *npub,
	const unsigned char *k
);

int crypto_aead_decrypt(
	unsigned char *m, unsigned long long *mlen,
	unsigned char *nsec,
	const unsigned char *c, unsigned long long clen,
	const unsigned char *ad, unsigned long long adlen,
	const unsigned char *npub,
	const unsigned char *k
);

static void random_uchar(unsigned char *str, unsigned long long len);
void fprint_bstr_orig(unsigned char *str, unsigned long long len);
void fprint_bstr_struc(unsigned int *str, unsigned int len);
/******************************/

/**
 * REMARKS
 * 1. In the structured version, `mlen` and `adlen` must be
 * multiple-of-4 numbers. This is because the bytetrings of the
 * `m` and `ad` are casted to the arrays of unsigned int.
 * All computations with bytes in the original version
 * are transformed to computations with unsigned int.
 *
 * 2. In the structured version, `mlen` and `adlen` are hardcoded
 * in the functions of encryption and decryption. These two variables
 * are treated as two constants when being obfuscated.
 * If you want to test with other values of `mlen` and `adlen`,
 * ensure that the values below and those in the structured version
 * are consistant.
 *
 * 3. NONCE_LEN and KEY_LEN are fixed to be 12 bytes and 16 bytes by default
 */

int main(){
  srand(time(NULL));

  // For original version
  unsigned long long mlen = 16, mlen1,
                     clen = mlen + 8,
                     adlen = 16;
  unsigned char m[mlen], m1[mlen],
                c[clen],
                ad[adlen],
                nonce[NONCE_LEN],
                key[KEY_LEN];

  // For structured version
  unsigned int mlen2 = mlen/4,
               clen2 = clen/4;
  unsigned int *m2 = (unsigned int *) m,
               c2[clen2],
               *ad2 = (unsigned int *) ad,
               *nonce2 = (unsigned int *) nonce,
               *key2 = (unsigned int *) key;


  for (int i=0; i<N_TEST; i++){
    if (i % 100 == 0) {
      printf("\rTest %7d/%d", i, N_TEST);
      fflush(stdout);
    }
    random_uchar(m, mlen);
    random_uchar(ad, adlen);
    random_uchar(nonce, NONCE_LEN);
    random_uchar(key, KEY_LEN);

    crypto_aead_encrypt(c, &clen, m, mlen, ad, adlen, NULL, nonce, key);
    crypto_aead_encrypt_struc(c2, m2, ad2, nonce2, key2);

    // check c = c2
    if (memcmp(c, c2, clen2) != 0){
      printf("\nError: encryption failed.\n");
      printf("----------------------------\n");
      printf("PT (Original)  : "); fprint_bstr_orig(m, mlen);
      printf("PT (Structured): "); fprint_bstr_struc(m2, mlen2);
      printf("CT (Original)  : "); fprint_bstr_orig(c, clen);
      printf("CT (Structured): "); fprint_bstr_struc(c2, clen2);
      printf("----------------------------\n");
      exit(EXIT_FAILURE);
    }

    int ret, ret2;
    ret  = crypto_aead_decrypt(m1, &mlen1, NULL, c, clen, ad, adlen, nonce, key);
    ret2 = crypto_aead_decrypt_struc(m2, c2, ad2, nonce2, key2);
    if (ret != 0 || ret2 != 0){
      printf("\nError: Decryption.....MAC Failed!\n");
      exit(EXIT_FAILURE);
    }

    if (mlen != mlen1 ||
        memcmp(m, m1, mlen) != 0 || memcmp(m, m2, mlen) != 0) {
      printf("\nError: Decryption.....Failed\n");
    }
  }
  printf("\rTest %d/%d ===> all tests correct.\n", N_TEST, N_TEST);

  return 0;
}

static void random_uchar(unsigned char *str, unsigned long long len){
  unsigned long long i;
  for (i=0; i<len; i++){
    str[i] = rand() % 256;
  }
}

void fprint_bstr_orig(unsigned char *str, unsigned long long len){
  unsigned long long i;
  for (i=0; i<len; i++){
    fprintf(stdout, "%02X", str[i]);
  }
  fprintf(stdout, "\n");
}

void fprint_bstr_struc(unsigned int *str, unsigned int len){
  unsigned int i;
  for (i=0; i<len; i++){
    fprintf(stdout, "%u ", str[i]);
  }
  fprintf(stdout, "\n");
}
