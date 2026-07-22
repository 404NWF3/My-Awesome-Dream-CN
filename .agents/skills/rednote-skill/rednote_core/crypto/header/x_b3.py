"""x-b3-traceid header generation — exact port of RedCrack header/X_B3.py."""

from __future__ import annotations

import random

from rednote_core.crypto.config import XB1_VALID_CHARS, XB1_TRACE_ID_LENGTH


def generate_x_b3_traceid() -> str:
    """Generate x-b3-traceid — 16 random chars from 'abcdef0123456789'.

    Exact port of RedCrack XHS_XB3_Encrypt.encrypt_header_xb3.
    """
    return "".join(random.choices(XB1_VALID_CHARS, k=XB1_TRACE_ID_LENGTH))
