"""websectiga cookie generation — exact port of RedCrack cookie/websectiga.py.

websectiga is NOT generated locally. It must be obtained by calling
POST https://as.xiaohongshu.com/api/sec/v1/scripting and decoding
the returned JSVMP data.
"""

from __future__ import annotations

import base64 as std_base64
import json
import re


def decode_websectiga(js_text: str) -> str:
    """Decode websectiga from the /api/sec/v1/scripting response.

    Exact port of RedCrack XHS_Websectiga_Encrypt.gen_websectiga.

    Args:
        js_text: The value of json['data']['data'] from the scripting API response.

    Returns:
        Decoded websectiga token string.
    """

    # Extract b and d fields
    b_match = re.search(r'"b":"(.*?)",', js_text)
    d_match = re.search(r'"d":(.*?)\}\)', js_text)
    if not b_match or not d_match:
        raise ValueError("Could not extract b/d from scripting response")
    b = b_match.group(1)
    d = json.loads(d_match.group(1))

    # Base64 decode and convert to logic list
    decode_logic_list = _decode_jsvmp_to_logic_list(b)

    # Get target decode list
    target_decode_list = decode_logic_list[d[92] : d[93] + 1]

    # Extract key — exact port: key = d[target_decode_list[675+i][2]]
    key = [d[target_decode_list[675 + i][2]] for i in range(0, 128, 2)]

    # Decode key: every 8 chars backwards in groups of 8
    decode_key = [chr(key[i + j]) for i in range(56, -1, -8) for j in range(8)]

    result = "".join(decode_key)
    # Filter non-ASCII characters that break HTTP headers
    return "".join(c for c in result if ord(c) < 128)


def _decode_jsvmp_to_logic_list(encoded_str: str) -> list[list[int]]:
    """Base64 decode and convert JSVMP encoded string to logic list.

    Exact port of RedCrack __decode_jsvmp_to_logic_list.
    """
    # Add padding
    padding = len(encoded_str) % 4
    if padding:
        encoded_str += "=" * (4 - padding)

    decoded_str = std_base64.b64decode(encoded_str).decode("utf-8", errors="replace")
    result = []
    current_chunk = []
    for char in decoded_str:
        if len(current_chunk) == 5:
            result.append(current_chunk)
            current_chunk = []
        char_code = ord(char)
        current_chunk.append(char_code - 1)
    if current_chunk:
        result.append(current_chunk)
    return result
