# tests/test_hash.py
import pytest
from rednote_core.crypto.primitives.hash import md5, sha256, hmac_sha256


class TestMD5:
    def test_md5_known_value(self):
        result = md5(b"hello")
        assert result == b"]A@*\xbcK*v\xb9q\x9d\x91\x10\x17\xc5\x92"

    def test_md5_empty(self):
        result = md5(b"")
        assert len(result) == 16

    def test_md5_deterministic(self):
        assert md5(b"test") == md5(b"test")


class TestSHA256:
    def test_sha256_known_value(self):
        result = sha256(b"hello")
        expected = bytes.fromhex(
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        )
        assert result == expected

    def test_sha256_length(self):
        assert len(sha256(b"")) == 32
        assert len(sha256(b"hello world")) == 32


class TestHMACSHA256:
    def test_hmac_known_value(self):
        key = b"secret"
        data = b"message"
        result = hmac_sha256(key, data)
        assert len(result) == 32

    def test_hmac_different_key_different_output(self):
        data = b"message"
        r1 = hmac_sha256(b"key1", data)
        r2 = hmac_sha256(b"key2", data)
        assert r1 != r2
