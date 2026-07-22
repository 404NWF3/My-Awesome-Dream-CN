"""Encoding primitives — exact ports from RedCrack.

Sources:
  - units/fuck_reverse_crypto/encoding.py
  - request/web/encrypt/xhs_diy_encode.py
"""

from __future__ import annotations

import base64 as std_base64


# ---------------------------------------------------------------------------
# RedCrack units/fuck_reverse_crypto/encoding.py
# ---------------------------------------------------------------------------

_STANDARD_ALPHABET = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def base64_encode(data: bytes, custom_alphabet: str | None = None) -> str:
    """Base64 encode bytes → str, optionally using a custom 64-char alphabet.

    Port of RedCrack units/fuck_reverse_crypto/encoding.py : base64_encode
    (adapted to return str for ergonomic use in header injection).
    """
    if custom_alphabet is not None:
        alphabet = custom_alphabet.encode()
        trans = bytes.maketrans(_STANDARD_ALPHABET, alphabet)
        return std_base64.b64encode(data).translate(trans).decode("ascii")
    return std_base64.b64encode(data).decode("ascii")


def base64_decode(encoded: str | bytes, custom_alphabet: str | None = None) -> bytes:
    """Base64 decode, optionally with the custom alphabet used to encode.

    Port of RedCrack units/fuck_reverse_crypto/encoding.py : base64_decode
    """
    if custom_alphabet is not None:
        alphabet = custom_alphabet.encode()
        trans = bytes.maketrans(alphabet, _STANDARD_ALPHABET)
        if isinstance(encoded, str):
            encoded = encoded.encode()
        return std_base64.b64decode(encoded.translate(trans))
    if isinstance(encoded, str):
        encoded = encoded.encode()
    return std_base64.b64decode(encoded)


# ---------------------------------------------------------------------------
# RedCrack request/web/encrypt/xhs_diy_encode.py
# ---------------------------------------------------------------------------


def triplet_to_base64(a: int, c: str) -> str:
    """Exact port of triplet_to_base64."""
    return c[(a >> 18) & 63] + c[(a >> 12) & 63] + c[(a >> 6) & 63] + c[a & 63]


def encode_chunk(a: list[int], e: int, r: int, c: str) -> str:
    """Exact port of encode_chunk."""
    d = []
    for f in range(e, r, 3):
        c_val = ((a[f] << 16) & 0xFF0000) + ((a[f + 1] << 8) & 0xFF00) + (a[f + 2] & 0xFF)
        d.append(triplet_to_base64(c_val, c))
    return "".join(d)


def b64_encode(a: bytes | bytearray | list[int], alphabet: str) -> str:
    """Custom Base64 encoder — exact port of RedCrack b64_encode.

    Used by x-s (X3_BASE64_TABLE) and x-s-common (BASE64_TABLE).
    """
    a_list = list(a) if isinstance(a, (bytes, bytearray)) else a
    c = alphabet
    r = len(a_list)
    d = r % 3
    f = []
    s = 16383
    u = 0
    l = r - d

    while u < l:
        end = min(u + s, l)
        f.append(encode_chunk(a_list, u, end, c))
        u += s

    if d == 1:
        e = a_list[r - 1]
        f.append(c[e >> 2] + c[(e << 4) & 63] + "==")
    elif d == 2:
        e = (a_list[r - 2] << 8) + a_list[r - 1]
        f.append(c[e >> 10] + c[(e >> 4) & 63] + c[(e << 2) & 63] + "=")

    return "".join(f)


def encode_utf8(a: str) -> list[int]:
    """URL-encoded string → list of byte values — exact port of RedCrack encode_utf8.

    Input is already URL-encoded (%xx sequences and plain ASCII chars).
    """
    url_encoded = a
    result = []
    i = 0
    while i < len(url_encoded):
        c = url_encoded[i]
        if c == "%":
            hex_str = url_encoded[i + 1 : i + 3]
            char_code = int(hex_str, 16)
            result.append(char_code)
            i += 3
        else:
            result.append(ord(c))
            i += 1
    return result


# ---------------------------------------------------------------------------
# Convenience aliases
# ---------------------------------------------------------------------------


def hex_encode(data: bytes) -> str:
    """Encode bytes to hex string (lowercase, no prefix)."""
    return data.hex()


def hex_decode(s: str) -> bytes:
    """Decode hex string to bytes."""
    s = s.lower()
    if s.startswith("0x"):
        s = s[2:]
    return bytes.fromhex(s)


def int_to_bytes(n: int, length: int) -> bytes:
    """Convert integer to big-endian bytes of fixed length."""
    return n.to_bytes(length, byteorder="big")


def bytes_to_int(data: bytes) -> int:
    """Convert big-endian bytes to integer."""
    return int.from_bytes(data, byteorder="big")


def xor_bytes(a: bytes, b: bytes) -> bytes:
    """XOR two byte sequences (must be same length)."""
    if len(a) != len(b):
        raise ValueError(f"Length mismatch: {len(a)} != {len(b)}")
    return bytes(x ^ y for x, y in zip(a, b))
