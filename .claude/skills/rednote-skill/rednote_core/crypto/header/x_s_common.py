"""x-s-common header generation — exact port of RedCrack header/X_S_Common.py.

x-s-common is a JSON payload → URL-encode → custom-utf8 → custom-base64 string
containing platform metadata, app version, a1, and an RC4-encrypted b1 (fingerprint subset).

The b1 sub-component encrypts a subset of the fingerprint dict with RC4
(key = "xhswebmplfbt"), then URL-encodes and custom-base64 encodes it.
"""

from __future__ import annotations

import json
import urllib.parse

from Cryptodome.Cipher import ARC4

from rednote_core.crypto.config import (
    GET_PLAT_FROM_CODE,
    LANGUAGE_VERSION,
    OS_SYSTEM,
    APP_ID,
    ARTIFACT_VERSION,
    BASE64_TABLE,
    B1_RC4_KEY,
)
from rednote_core.crypto.primitives.encoding import b64_encode, encode_utf8


def _unsigned_right_shift(value: int, shift: int) -> int:
    """JavaScript-style unsigned right shift (32-bit)."""
    return (value & 0xFFFFFFFF) >> shift


def _diy_mrc(e: str) -> int:
    """Compute custom MRC (CRC32 variant) — exact port of XHS_XSC_Encrypt.__diy_mrc."""

    def jsint(num: int) -> int:
        """JS int conversion."""
        return num % (2**32) if num >= 2**31 else num - 2**32

    # Build MRC table
    mrc_list = []
    for i in range(255, -1, -1):
        j = i
        for _ in range(8, 0, -1):
            j = _unsigned_right_shift(j, 1) ^ 0xEDB88320 if j & 1 else _unsigned_right_shift(j, 1)
        mrc_list.insert(0, _unsigned_right_shift(j, 0))

    # Compute result
    i = -1
    for r in e:
        i = mrc_list[255 & i ^ ord(r)] ^ _unsigned_right_shift(i, 8)

    return -1 ^ jsint(i) ^ 0xEDB88320


def _encrypt_b1(fp: dict) -> str:
    """Encrypt b1 (fingerprint subset) — exact port of XHS_XSC_Encrypt.__encrypt_b1.

    b1 selects specific keys from the fingerprint dict (x33-x38, x42-x46, x48-x52, x82),
    JSON-serializes them, encrypts with RC4, URL-encodes, then custom-base64 encodes.
    """
    b1_keys = [
        "x33", "x34", "x35", "x36", "x37", "x38", "x39",
        "x42", "x43", "x44", "x45", "x46",
        "x48", "x49", "x50", "x51", "x52",
        "x82",
    ]

    b1_fp = {k: fp.get(k, "") for k in b1_keys}

    b1_fp_jsonify = json.dumps(b1_fp, separators=(",", ":"), ensure_ascii=False)

    # RC4 encrypt
    cipher = ARC4.new(B1_RC4_KEY)
    ciphertext = cipher.encrypt(b1_fp_jsonify.encode("utf-8"))
    # Decode as latin1 for URL encoding
    ciphertext_str = ciphertext.decode("latin1")

    encoded_url = urllib.parse.quote(ciphertext_str, safe="!*'()~_-")

    # Build byte list: %xx → raw byte, else ordinal
    b = []
    for c in encoded_url.split("%")[1:]:
        chars = list(c)
        b.append(int("".join(chars[:2]), 16))
        b.extend(ord(j) for j in chars[2:])

    b1 = b64_encode(bytearray(b), "ZmserbBoHQtNP+wOcza/LpngG8yJq42KWYj0DSfdikx3VT16IlUAFM97hECvuRX5")
    return b1


def generate_x_s_common(
    cookie_a1: str,
    cookie_loadts: int,
    uri: str = "",
    fp: dict | None = None,
) -> str:
    """Generate x-s-common header — exact port of XHS_XSC_Encrypt.encrypt_headers_xsc.

    Args:
        cookie_a1: The a1 cookie value
        cookie_loadts: The loadts cookie value (page load timestamp, ms)
        uri: URL path (not actually used in xsc, kept for API consistency)
        fp: Fingerprint dict from XhsFpGenerator. If None, a minimal placeholder is used.

    Returns:
        x-s-common header value (custom-base64 string)
    """
    if fp is None:
        fp = {
            "x33": "0", "x34": "0", "x35": "0", "x36": "1", "x37": "0|0|0|0|0|0|0|0|0|1|0|0|0|0|0|0|0|0|1|0|0|0|0|0",
            "x38": "0|0|1|0|1|0|0|0|0|0|1|0|1|0|1|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0",
            "x39": "0",
            "x42": "3.5.4", "x43": "Canvas not supported",
            "x44": str(int(__import__("time").time() * 1000)),
            "x45": "__SEC_CAV__1-1-1-1-1|__SEC_WSA__|",
            "x46": "false",
            "x48": "", "x49": "{list:[],type:}", "x50": "", "x51": "", "x52": "",
            "x82": "_0x17a2|_0x1954",
        }

    b1 = _encrypt_b1(fp)

    source_text = {
        "s0": GET_PLAT_FROM_CODE,
        "s1": "",
        "x0": "1",  # localStorage.getItem("b1b1")
        "x1": LANGUAGE_VERSION,
        "x2": OS_SYSTEM,
        "x3": APP_ID,
        "x4": ARTIFACT_VERSION,
        "x5": cookie_a1,
        "x6": "",
        "x7": "",
        "x8": b1,
        "x9": int(_diy_mrc("" + "" + b1)),
        "x10": fp.get("x39", "0"),
        "x11": "normal",
    }

    # JSON → URL encode → custom utf8 → custom base64
    p_json = json.dumps(source_text, separators=(",", ":"), ensure_ascii=False)
    p_quoted = urllib.parse.quote(p_json, safe="-_.!~*'()")
    p_utf8 = encode_utf8(p_quoted)
    p_b64 = b64_encode(p_utf8, BASE64_TABLE)

    return p_b64
