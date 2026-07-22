"""Hash function primitives — exact ports from RedCrack.

Sources:
  - units/fuck_reverse_crypto/hash_functions.py
  - request/web/encrypt/header/X_S.py (__diy_hasher)
"""

from __future__ import annotations

import hashlib
import hmac as hmac_module
import zlib


# ---------------------------------------------------------------------------
# RedCrack units/fuck_reverse_crypto/hash_functions.py
# ---------------------------------------------------------------------------


def md5(data: bytes) -> bytes:
    """Compute MD5 hash of data — returns raw bytes (16 bytes)."""
    return hashlib.md5(data).digest()


def md5_hex(data: str) -> str:
    """Compute MD5 hash of string — returns hex string.

    Port of RedCrack md5_encode.
    """
    return hashlib.md5(data.encode()).hexdigest()


def sha256(data: bytes) -> bytes:
    """Compute SHA-256 hash — returns raw bytes (32 bytes)."""
    return hashlib.sha256(data).digest()


def sha256_hex(data: str) -> str:
    """Compute SHA-256 hash of string — returns hex string.

    Port of RedCrack sha256_encode.
    """
    return hashlib.sha256(data.encode()).hexdigest()


def sha1_hex(data: str) -> str:
    """Compute SHA-1 hash of string — returns hex string.

    Port of RedCrack sha1_encode.
    """
    return hashlib.sha1(data.encode()).hexdigest()


def crc32_encode(data: str) -> int:
    """Compute CRC32 of string — returns int.

    Port of RedCrack crc32_encode.
    """
    return zlib.crc32(data.encode())


def hmac_sha256(key: bytes, data: bytes) -> bytes:
    """Compute HMAC-SHA256 — returns raw bytes (32 bytes)."""
    return hmac_module.new(key, data, hashlib.sha256).digest()


# ---------------------------------------------------------------------------
# RedCrack request/web/encrypt/header/X_S.py — __diy_hasher
# ---------------------------------------------------------------------------


def _u32_add(a: int, b: int) -> int:
    """32-bit unsigned addition."""
    return (a + b) & 0xFFFFFFFF


def _js_left_rotate(n: int, d: int) -> int:
    """JavaScript-style left rotate (32-bit)."""
    return ((n << d) | (n >> (32 - d))) & 0xFFFFFFFF


def diy_hasher(data: list[int]) -> bytes:
    """Custom hash function — exact port of RedCrack XHS_XS_Encrypt.__diy_hasher.

    Used in the x-s signature x3 sub-component.
    Returns 16 bytes (4 × u32 little-endian).
    """
    data_length = len(data)

    # Initialize s1, s2, s3, s4
    s1 = 1831565813 ^ data_length
    s2 = 461845907 ^ (data_length << 8)
    s3 = 2246822507 ^ (data_length << 16)
    s4 = 3266489909 ^ (data_length << 24)

    for i in range(0, len(data), 8):
        v0 = int.from_bytes(bytes(data[i : i + 4]), byteorder="little")
        v1 = int.from_bytes(bytes(data[i + 4 : i + 8]), byteorder="little")

        s1 = _js_left_rotate(_u32_add(s1, v0) ^ s3, 7)
        s2 = _js_left_rotate(_u32_add(s2 ^ v0, s4), 11)
        s3 = _js_left_rotate(_u32_add(s3, v1) ^ s1, 13)
        s4 = _js_left_rotate(_u32_add(s4 ^ v1, s2), 17)

    t1 = s1 ^ data_length
    t2 = t1 ^ s2
    t3 = _u32_add(t2, s3)
    t4 = t3 ^ s4

    rot_t1 = _js_left_rotate(t1, 9)
    rot_t2 = _js_left_rotate(t2, 13)
    rot_t3 = _js_left_rotate(t3, 17)
    rot_t4 = _js_left_rotate(t4, 19)

    p1 = _u32_add(rot_t1, rot_t3)
    p2 = rot_t2 ^ rot_t4
    p3 = _u32_add(rot_t3, p1)
    p4 = rot_t4 ^ p2

    return (
        p1.to_bytes(4, byteorder="little")
        + p2.to_bytes(4, byteorder="little")
        + p3.to_bytes(4, byteorder="little")
        + p4.to_bytes(4, byteorder="little")
    )
