"""Xiaohongshu encryption constants — exact values from RedCrack web_encrypt_config.ini."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# [XHS_VERSION]
# ---------------------------------------------------------------------------
APP_ID = "xhs-pc-web"
LANGUAGE_VERSION = "4.3.5"
ARTIFACT_VERSION = "6.12.3"
OS_SYSTEM = "Windows"
GET_PLAT_FROM_CODE = 5
BASE64_TABLE = "ZmserbBoHQtNP+wOcza/LpngG8yJq42KWYj0DSfdikx3VT16IlUAFM97hECvuRX5"

# ---------------------------------------------------------------------------
# [XS_ENCRYPT]
# ---------------------------------------------------------------------------
X3_BASE64_TABLE = "MfgqrsbcyzPQRStuvC7mn501HIJBo2DEFTKdeNOwxWXYZap89+/A4UVLhijkl63G"
X3_PREFIX = "mns0301_"

# Exact XOR key (144 bytes)
XOR_KEY = [
    113, 163, 2, 37, 119, 147, 39, 29, 221, 39, 59, 206, 227, 228, 185, 141,
    157, 121, 53, 225, 218, 51, 245, 118, 94, 46, 168, 175, 182, 220, 119, 165,
    26, 73, 157, 35, 182, 124, 32, 102, 0, 37, 134, 12, 191, 19, 212, 84,
    13, 146, 73, 127, 88, 104, 108, 87, 78, 80, 143, 70, 225, 149, 99, 68,
    243, 145, 57, 191, 79, 175, 34, 163, 238, 241, 32, 183, 146, 88, 20, 91,
    47, 235, 81, 147, 182, 71, 134, 105, 150, 18, 152, 231, 155, 237, 202, 100,
    110, 26, 105, 58, 146, 97, 84, 165, 167, 161, 189, 28, 240, 222, 219, 116,
    47, 145, 122, 116, 122, 30, 56, 139, 35, 79, 34, 119, 81, 109, 183, 17,
    96, 53, 67, 151, 48, 250, 97, 233, 130, 42, 14, 202, 123, 255, 114, 216,
]

# ---------------------------------------------------------------------------
# [XSC_ENCRYPT]
# ---------------------------------------------------------------------------
B1_RC4_KEY = b"xhswebmplfbt"

# ---------------------------------------------------------------------------
# [A1_ENCRYPT]
# ---------------------------------------------------------------------------
A1_VALID_CHARS = "abcdefghijklmnopqrstuvwxyz1234567890"
A1_TRACE_ID_LENGTH = 30

# ---------------------------------------------------------------------------
# [XB1_ENCRYPT] (used by x-b3-traceid and gid)
# ---------------------------------------------------------------------------
XB1_VALID_CHARS = "abcdef0123456789"
XB1_TRACE_ID_LENGTH = 16

# ---------------------------------------------------------------------------
# [GID_ENCRYPT]
# ---------------------------------------------------------------------------
GID_DES_KEY = b"zbp30y86"
GID_URL = "https://as.xiaohongshu.com/api/sec/v1/shield/webprofile"
GID_DATA_PLATFORM = "Windows"
GID_DATA_SDK_VERSION = "4.2.6"
GID_DATA_SVN = "2"

# ---------------------------------------------------------------------------
# [XRAP_ENCRYPT]
# ---------------------------------------------------------------------------
XRAP_ENCRYPT_URLS = [
    "https://edith.xiaohongshu.com/api/sns/web/v1/homefeed",
    "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes",
    "https://edith.xiaohongshu.com/api/sns/web/v1/user_posted",
    "https://edith.xiaohongshu.com/api/sns/web/v1/feed",
    "https://edith.xiaohongshu.com/api/sns/web/v1/comment/post",
]

# ---------------------------------------------------------------------------
# [HEADER] — default request headers from RedCrack
# ---------------------------------------------------------------------------
# Minimal headers — matches curl behavior to avoid CDN WAF blocking.
# Browser-fingerprint headers (sec-ch-ua*, sec-fetch-*, priority) are omitted
# because Akamai/TencentEdgeOne reject requests that lack a full browser cookie set.
DEFAULT_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "content-type": "application/json;charset=UTF-8",
    "origin": "https://www.xiaohongshu.com",
    "referer": "https://www.xiaohongshu.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}
