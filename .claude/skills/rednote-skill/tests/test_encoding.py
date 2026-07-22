# tests/test_encoding.py
import pytest
from rednote_core.crypto.primitives.encoding import (
    base64_encode,
    base64_decode,
    hex_encode,
    hex_decode,
    int_to_bytes,
    bytes_to_int,
    xor_bytes,
)


class TestBase64:
    def test_roundtrip(self):
        original = b"Hello, World!"
        encoded = base64_encode(original)
        decoded = base64_decode(encoded)
        assert decoded == original

    def test_encode_known(self):
        result = base64_encode(b"f")
        # RedCrack port returns bytes; accept both for compat
        if isinstance(result, bytes):
            result = result.decode("ascii")
        assert result == "Zg=="

    def test_decode_known(self):
        assert base64_decode("Zg==") == b"f"


class TestHex:
    def test_roundtrip(self):
        original = b"\x00\xff\xab\x12"
        encoded = hex_encode(original)
        decoded = hex_decode(encoded)
        assert decoded == original

    def test_encode_known(self):
        assert hex_encode(b"\xab\xcd") == "abcd"

    def test_decode_known(self):
        assert hex_decode("abcd") == b"\xab\xcd"


class TestIntBytes:
    def test_roundtrip(self):
        n = 123456789
        b = int_to_bytes(n, 8)
        assert bytes_to_int(b) == n

    def test_fixed_length(self):
        b = int_to_bytes(5, 4)
        assert len(b) == 4
        assert b == b"\x00\x00\x00\x05"


class TestXor:
    def test_xor_basic(self):
        a = bytes([0x0F, 0xF0, 0xAA, 0x55])
        b = bytes([0xFF, 0x0F, 0x55, 0xAA])
        result = xor_bytes(a, b)
        expected = bytes([0xF0, 0xFF, 0xFF, 0xFF])
        assert result == expected

    def test_xor_same_length(self):
        with pytest.raises(ValueError):
            xor_bytes(b"abc", b"ab")
