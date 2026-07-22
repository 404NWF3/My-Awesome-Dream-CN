"""a1 and webId cookie generation — exact port of RedCrack cookie/a1_and_webId.py."""

from __future__ import annotations

import random
import time

from rednote_core.crypto.config import A1_VALID_CHARS, A1_TRACE_ID_LENGTH, GET_PLAT_FROM_CODE
from rednote_core.crypto.primitives.hash import crc32_encode, md5_hex


def generate_a1() -> str:
    """Generate the a1 device identifier cookie.

    Exact port of RedCrack XHS_A1_And_WebId_Encrypt.encrypt_cookie_a1_and_webId.
    Format: hex_timestamp(13) + 30 rand chars + platform_code(1) + "0" + "000" + crc32 → truncate to 52.
    """
    hex_data = hex(int(time.time() * 1000))[2:]  # "18f..." — 11-12 chars

    random_string = "".join(random.choices(A1_VALID_CHARS, k=A1_TRACE_ID_LENGTH))

    text = hex_data + random_string + str(GET_PLAT_FROM_CODE) + "0" + "000"

    # CRC32 checksum
    crc = str(crc32_encode(text))

    a1 = (text + crc)[:52]
    return a1


def generate_web_id(a1: str = "") -> str:
    """Generate the webId session identifier cookie.

    Exact port of RedCrack: webId = MD5(a1).
    """
    if not a1:
        a1 = generate_a1()
    return md5_hex(a1)
