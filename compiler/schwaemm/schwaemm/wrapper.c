#include <stdlib.h>
#include "schwaemm.h"

void schwaemm128128_encrypt(
	char **c, long long *clen,
	const char *m, long long mlen,
	const char *ad, long long adlen,
	const char *nonce, const char *key
) {
	*clen = mlen + SCHWAEMM_TAG_BYTES;
	*c = malloc(*clen);
	if (!*c) {
		return;
	}
	int ret = crypto_aead_encrypt(
		(unsigned char *)*c, (unsigned long long*)clen,
		(const unsigned char *)m, (unsigned long long)mlen,
		(const unsigned char *)ad, (unsigned long long)adlen,
		(const unsigned char *)NULL, (const unsigned char *)nonce, (const unsigned char *)key
	);
	if (ret != 0) {
		free(*c);
		*c = NULL;
		return;
	}
	return;
}

void schwaemm128128_decrypt(
	char **m, long long *mlen,
	const char *c, long long clen,
	const char *ad, long long adlen,
	const char *nonce, const char *key
) {
	*mlen = clen - SCHWAEMM_TAG_BYTES;
	if (mlen < 0) {
		*m = NULL;
		return;
	}
	*m = malloc(*mlen);
	if (!*m) {
		return;
	}
	int ret = crypto_aead_decrypt(
		(unsigned char *)*m, (unsigned long long*)mlen,
		(unsigned char *)NULL,
		(const unsigned char *)c, (unsigned long long)clen,
		(const unsigned char *)ad, (unsigned long long)adlen,
		(const unsigned char *)nonce, (const unsigned char *)key
	);
	if (ret != 0) {
		free(*m);
		*m = NULL;
		return;
	}
	return;
}

// int crypto_aead_encrypt(
// 	UChar *c, ULLInt *clen, const UChar *m, ULLInt mlen,
//   	const UChar *ad, ULLInt adlen, const UChar *nsec, const UChar *npub,
//   	const UChar *k);

// int crypto_aead_decrypt(
// 	UChar *m, ULLInt *mlen, UChar *nsec, const UChar *c,
//   	ULLInt clen, const UChar *ad, ULLInt adlen, const UChar *npub,
//   	const UChar *k);