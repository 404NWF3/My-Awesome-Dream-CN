# tests/test_asymmetric.py
import pytest
from rednote_core.crypto.primitives.asymmetric import (
    rsa_encrypt_oaep,
    rsa_encrypt_pkcs1v15,
)

# Test RSA public key in PEM format (1024-bit for test speed)
TEST_PUBKEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC0IGRgV2WJ1qFJQHqxVxKbVXQD
zJsnHmKfLIFMdy4IfwYBsOJcEkPKLMPLMDNk6iFqUzOBBuEFxwp1fYKh6pLBlIIF
x4LCloMvAYgFyJmJhKWOoFmLDgEuxKfCLGjFqrYvPkxozLySJMQpibEVhzKbXQSD
zwMhKqkP5rCFEWKNfQIDAQAB
-----END PUBLIC KEY-----"""


class TestRSA:
    def test_oaep_encrypt(self):
        plaintext = b"hello"
        result = rsa_encrypt_oaep(TEST_PUBKEY, plaintext)
        assert isinstance(result, bytes)
        assert len(result) == 128  # 1024-bit RSA = 128 bytes output

    def test_oaep_empty(self):
        result = rsa_encrypt_oaep(TEST_PUBKEY, b"")
        assert isinstance(result, bytes)
        assert len(result) == 128

    def test_pkcs1v15_encrypt(self):
        plaintext = b"hello"
        result = rsa_encrypt_pkcs1v15(TEST_PUBKEY, plaintext)
        assert isinstance(result, bytes)
        assert len(result) == 128

    def test_different_inputs_different_outputs(self):
        r1 = rsa_encrypt_oaep(TEST_PUBKEY, b"aaa")
        r2 = rsa_encrypt_oaep(TEST_PUBKEY, b"bbb")
        assert r1 != r2
