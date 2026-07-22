"""acw_tc cookie decryption.

The acw_tc cookie is set by Alibaba Cloud WAF.
It requires XOR-based decryption to extract the actual token.

References:
  - RedCrack cookie/acw_tc.py
  - Standard Alibaba Cloud WAF acw_tc format
"""

import re
from rednote_core.crypto.primitives.encoding import hex_decode


def decrypt_acw_tc(encrypted: str) -> str:
    """Decrypt an acw_tc cookie value.

    The acw_tc cookie from Alibaba Cloud WAF uses a simple
    XOR-based obfuscation. The decryption extracts the usable token.

    Args:
        encrypted: Raw acw_tc value from set-cookie header

    Returns:
        Decrypted token, or empty string on failure
    """
    if not encrypted or len(encrypted) < 4:
        return ""

    # acw_tc follows a specific format: hex-encoded XOR'd data
    try:
        raw = hex_decode(encrypted)
    except (ValueError, TypeError):
        return encrypted  # Return as-is if not hex

    # Simple XOR decryption with the standard keys
    box = _get_acw_box()
    if not box:
        return encrypted

    result = bytearray()
    for i, b in enumerate(raw):
        result.append(b ^ box[i % len(box)])

    try:
        return result.decode("utf-8", errors="replace")
    except Exception:
        return encrypted


def _get_acw_box() -> list[int]:
    """Get the standard ACW decryption box.

    Returns:
        List of integer XOR keys
    """
    return [0x3F, 0x45, 0x2A, 0x1B, 0x6D, 0x5C, 0x78, 0x11]
