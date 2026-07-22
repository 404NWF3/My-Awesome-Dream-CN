"""gid cookie generation — exact port of RedCrack cookie/gid_webprofile_data.py.

gid is obtained by calling POST https://as.xiaohongshu.com/api/sec/v1/shield/webprofile
with a DES-encrypted fingerprint payload. The gid value is returned in set-cookie.
"""

from __future__ import annotations

import base64 as std_base64
import json

from Cryptodome.Cipher import DES

from rednote_core.crypto.config import (
    GID_DES_KEY,
    GID_URL,
    GID_DATA_PLATFORM,
    GID_DATA_SDK_VERSION,
    GID_DATA_SVN,
)


def _zero_pad(data: bytes, block_size: int = 8) -> bytes:
    """Zero-pad to block size — exact port of zero_pad."""
    pad_len = block_size - len(data) % block_size
    return data + b"\x00" * pad_len


def _encrypt_profile_data(fp: dict) -> str:
    """Encrypt fingerprint data for the gid API — exact port of __encrypt_profileData.

    Returns hex-encoded ciphertext.
    """
    fp_jsonify = json.dumps(fp, separators=(",", ":"), ensure_ascii=False)
    fp_base64 = std_base64.b64encode(fp_jsonify.encode())
    cipher = DES.new(GID_DES_KEY, DES.MODE_ECB)
    ciphertext = cipher.encrypt(_zero_pad(fp_base64))
    return ciphertext.hex()


def build_gid_request(fp: dict) -> tuple[str, dict]:
    """Build the (url, data) for the shield/webprofile API call.

    Exact port of RedCrack XHS_Gid_Webprofile_Data_Encrypt.gen_gid_webprofile_data.

    Args:
        fp: Fingerprint dict (from XhsFpGenerator)

    Returns:
        (url, data) tuple for POST request
    """
    data = {
        "platform": GID_DATA_PLATFORM,
        "profileData": _encrypt_profile_data(fp),
        "sdkVersion": GID_DATA_SDK_VERSION,
        "svn": GID_DATA_SVN,
    }
    return GID_URL, data
