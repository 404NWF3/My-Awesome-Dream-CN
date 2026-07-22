"""Cookie generation module — exact ports from RedCrack:

  - a1 and webId:  locally generated (CRC32 + MD5)
  - websectiga:    obtained via POST /api/sec/v1/scripting
  - gid:           obtained via POST /api/sec/v1/shield/webprofile (DES-encrypted fp)
  - acw_tc:        obtained from server set-cookie (WAF token)
  - web_session:   obtained from login (QR code scan)
  - sec_poison_id: obtained from scripting API
"""

from rednote_core.crypto.cookie.a1_webid import generate_a1, generate_web_id
from rednote_core.crypto.cookie.gid import build_gid_request
from rednote_core.crypto.cookie.websectiga import decode_websectiga

# Re-export for convenience — generate_gid is no longer local-only
# Instead, gid is obtained from the shield/webprofile API response.

__all__ = [
    "generate_a1",
    "generate_web_id",
    "build_gid_request",
    "decode_websectiga",
]
