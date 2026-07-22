# tests/test_symmetric.py
import pytest
from rednote_core.crypto.primitives.symmetric import (
    aes_cbc_encrypt,
    aes_cbc_decrypt,
    aes_ecb_encrypt,
    aes_ecb_decrypt,
)


class TestAESCBC:
    def test_encrypt_decrypt_roundtrip(self):
        key = b"0123456789abcdef"  # 16 bytes for AES-128
        iv = b"fedcba9876543210"   # 16 bytes
        plaintext = b"Hello, World! This is test data."

        ciphertext = aes_cbc_encrypt(key, iv, plaintext)
        decrypted = aes_cbc_decrypt(key, iv, ciphertext)
        assert decrypted == plaintext

    def test_pkcs7_padding(self):
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"
        # 16 bytes should pad to 32
        plaintext = b"0123456789abcdef"

        ciphertext = aes_cbc_encrypt(key, iv, plaintext)
        assert len(ciphertext) == 32
        decrypted = aes_cbc_decrypt(key, iv, ciphertext)
        assert decrypted == plaintext

    def test_empty_string(self):
        key = b"0123456789abcdef"
        iv = b"fedcba9876543210"
        plaintext = b""

        ciphertext = aes_cbc_encrypt(key, iv, plaintext)
        decrypted = aes_cbc_decrypt(key, iv, ciphertext)
        assert decrypted == plaintext


class TestAESECB:
    def test_encrypt_decrypt_roundtrip(self):
        key = b"0123456789abcdef"
        plaintext = b"Hello, World! Test."

        ciphertext = aes_ecb_encrypt(key, plaintext)
        decrypted = aes_ecb_decrypt(key, ciphertext)
        assert decrypted == plaintext

    def test_pkcs7_padding(self):
        key = b"0123456789abcdef"
        plaintext = b"0123456789abcdef"

        ciphertext = aes_ecb_encrypt(key, plaintext)
        assert len(ciphertext) == 32
        decrypted = aes_ecb_decrypt(key, ciphertext)
        assert decrypted == plaintext
