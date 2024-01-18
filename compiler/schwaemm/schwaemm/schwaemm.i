%module schwaemm

%{
#define SWIG_PYTHON_STRICT_BYTE_CHAR
void schwaemm128128_encrypt(
	char **c, long long *clen,
	const char *m, long long mlen,
	const char *ad, long long adlen,
	const char *nonce, const char *key
);

void schwaemm128128_decrypt(
	char **m, long long *mlen,
	const char *c, long long clen,
	const char *ad, long long adlen,
	const char *nonce, const char *key
);
%}

%include "cstring.i"

%cstring_output_allocate_size(char **c, long long *clen, free(*$1));
%apply (char *STRING, size_t LENGTH) { (const char *m, long long mlen) };
%apply (char *STRING, size_t LENGTH) { (const char *ad, long long adlen) };
void schwaemm128128_encrypt(
	char **c, long long *clen,
	const char *m, long long mlen,
	const char *ad, long long adlen,
	const char *nonce, const char *key
);

%cstring_output_allocate_size(char **m, long long *mlen, free(*$1));
%apply (char *STRING, size_t LENGTH) { (const char *c, long long clen) };
%apply (char *STRING, size_t LENGTH) { (const char *ad, long long adlen) };
void schwaemm128128_decrypt(
	char **m, long long *mlen,
	const char *c, long long clen,
	const char *ad, long long adlen,
	const char *nonce, const char *key
);
