from schwaemm import schwaemm128128_encrypt, schwaemm128128_decrypt


msg = b"message"
ad = b"ad"
nonce = b"N"*16
key = b"K"*16
ct = schwaemm128128_encrypt(msg, ad, nonce, key)
print("ct", ct)
pt = schwaemm128128_decrypt(ct, ad, nonce, key)
print("pt", pt)


Key = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
Nonce = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
PT = bytes.fromhex("000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F")
AD = bytes.fromhex("000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F")
CT = bytes.fromhex("9C8A78029D70397B63A4CA18C8248B7A5D5DC1DE714CB01AA58EF58DB020C7F6033BF5CB08FA0F06F8F990D07723823F")
assert CT == schwaemm128128_encrypt(PT, AD, Nonce, Key)
assert PT == schwaemm128128_decrypt(CT, AD, Nonce, Key)
print("Ok!")
