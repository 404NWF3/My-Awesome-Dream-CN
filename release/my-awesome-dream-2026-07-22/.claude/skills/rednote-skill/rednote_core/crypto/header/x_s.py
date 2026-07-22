"""x-s request signature header generation — exact port of RedCrack header/X_S.py.

The x-s signature is the primary request authentication header.
Format: "XYS_" + custom_base64(json_payload)
  where json_payload has keys x0, x1, x2, x3, x4
  and x3 is the mns0301_-prefixed encrypted sub-component.

The x3 sub-component uses:
  1. Custom hasher (diy_hasher)
  2. XOR key obfuscation (144-byte XOR_KEY)
  3. Custom Base64 encoding (X3_BASE64_TABLE)
  4. "mns0301_" prefix
"""

from __future__ import annotations

import hashlib
import json
import random
import time
import urllib.parse

from rednote_core.crypto.config import (
    APP_ID,
    LANGUAGE_VERSION,
    OS_SYSTEM,
    BASE64_TABLE,
    X3_BASE64_TABLE,
    X3_PREFIX,
    XOR_KEY,
)
from rednote_core.crypto.primitives.encoding import b64_encode, encode_utf8
from rednote_core.crypto.primitives.hash import diy_hasher


def _u32_add(a: int, b: int) -> int:
    """32-bit unsigned addition."""
    return (a + b) & 0xFFFFFFFF


def _js_left_rotate(n: int, d: int) -> int:
    """JavaScript-style left rotate (32-bit)."""
    return ((n << d) | (n >> (32 - d))) & 0xFFFFFFFF


def _encrypt_headers_x3(
    cookie_a1: str,
    cookie_loadts: int,
    uri: str = "",
    params: dict | None = None,
    data: dict | None = None,
) -> str:
    """Encrypt the x3 sub-component — exact port of XHS_XS_Encrypt.__encrypt_headers_x3.

    Args:
        cookie_a1: The a1 cookie value
        cookie_loadts: The loadts cookie value (page load timestamp, ms)
        uri: URL path (e.g. "/api/sns/web/v1/homefeed")
        params: GET query params dict
        data: POST body dict

    Returns:
        "mns0301_<base64>" encrypted string
    """
    if params:
        query_string = urllib.parse.urlencode(params).replace("%2C", ",")
        uri = f"{uri}?{query_string}"

    md5_url_params = hashlib.md5(uri.encode()).hexdigest()

    if data is not None:
        data_str = json.dumps(data, separators=(",", ":"))
        uri = uri + data_str

    md5_url_params_data = hashlib.md5(uri.encode()).hexdigest()

    # Fixed
    encrypt_part1_4 = [121, 104, 96, 41]

    # Random u32
    random_num = int(random.random() * 4294967295)
    encrypt_part2_4 = list(random_num.to_bytes(4, byteorder="little"))

    # Timestamp (ms) as 8 bytes little-endian
    timestamp = int(time.time() * 1000)
    encrypt_part3_8 = list(timestamp.to_bytes(8, byteorder="little"))

    # loadts as 8 bytes little-endian
    encrypt_part4_8 = list(cookie_loadts.to_bytes(8, byteorder="little"))

    # Random 1-99
    num = int(random.random() * 99) + 1
    encrypt_part5_4 = list(num.to_bytes(4, byteorder="little"))

    # Object.getOwnPropertyNames(window).length — fixed 1352
    encrypt_part6_4 = list((1352).to_bytes(4, byteorder="little"))

    # URI length after utf8 encoding
    num = len(uri.encode("utf-8"))
    encrypt_part7_4 = list(num.to_bytes(4, byteorder="little"))

    # MD5(url+params+data) first 8 bytes XOR'd with random_num
    encrypt_part8_8 = [
        b ^ (random_num & 255) for b in list(bytes.fromhex(md5_url_params_data))
    ][:8]

    # a1: len + bytes
    byte_array = list(cookie_a1.encode("utf-8"))
    encrypt_part9_53 = [len(byte_array)] + byte_array

    # appId: len + bytes
    byte_array = list(APP_ID.encode("utf-8"))
    encrypt_part10_11 = [len(byte_array)] + byte_array

    # Fixed 16 bytes
    encrypt_part11_16 = [
        1,
        (random_num & 255) ^ 115,
        249,
        65,
        103,
        103,
        201,
        181,
        131,
        99,
        94,
        7,
        68,
        250,
        132,
        21,
    ]

    # Fixed 4 bytes
    encrypt_part12_4 = [2, 97, 51, 16]

    # Hash (timestamp + MD5(url+params)) XOR'd with random_num
    ts_and_md5_hash = list(
        diy_hasher(encrypt_part3_8 + list(bytes.fromhex(md5_url_params)))
    )
    encrypt_part13_16 = [i ^ (random_num & 255) for i in ts_and_md5_hash]

    # Concatenate all parts
    encrypt_144_old = (
        encrypt_part1_4
        + encrypt_part2_4
        + encrypt_part3_8
        + encrypt_part4_8
        + encrypt_part5_4
        + encrypt_part6_4
        + encrypt_part7_4
        + encrypt_part8_8
        + encrypt_part9_53
        + encrypt_part10_11
        + encrypt_part11_16
        + encrypt_part12_4
        + encrypt_part13_16
    )

    # XOR with the key
    encrypt_144_new = [i ^ j for i, j in zip(encrypt_144_old, XOR_KEY)]

    # Encode with x3_base64_table + prefix
    encoded_str = X3_PREFIX + b64_encode(bytes(encrypt_144_new), X3_BASE64_TABLE)
    return encoded_str


def generate_x_s(
    cookie_a1: str,
    cookie_loadts: int,
    uri: str = "",
    params: dict | None = None,
    data: str | dict | None = None,
) -> str:
    """Generate the x-s signature header — exact port of XHS_XS_Encrypt.encrypt_headers_xs.

    Args:
        cookie_a1: Cookie a1 value
        cookie_loadts: Cookie loadts value (page load time in ms as int)
        uri: URL path, e.g. "/api/sns/web/v1/homefeed"
        params: GET query params dict (optional)
        data: POST body — str (JSON string) or dict (converted to JSON)

    Returns:
        x-s header value: "XYS_<base64>"
    """
    # Parse data if it's a string
    data_dict = None
    if data is not None:
        if isinstance(data, str) and data.strip():
            try:
                data_dict = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                data_dict = data  # pass as-is
        elif isinstance(data, dict):
            data_dict = data
        else:
            data_dict = None

    p = {
        "x0": LANGUAGE_VERSION,
        "x1": APP_ID,
        "x2": OS_SYSTEM,
        "x3": _encrypt_headers_x3(cookie_a1, cookie_loadts, uri, params, data_dict),
        "x4": "" if data_dict is None else "object",
    }

    # JSON → URL encode → custom utf8 → custom base64
    p_json = json.dumps(p, separators=(",", ":"))
    p_quoted = urllib.parse.quote(p_json, safe="-_.!~*'()")
    p_utf8 = encode_utf8(p_quoted)
    p_b64 = b64_encode(p_utf8, BASE64_TABLE)

    return "XYS_" + p_b64
