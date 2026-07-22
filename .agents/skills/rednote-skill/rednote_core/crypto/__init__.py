"""RedNote crypto module — cookie generation and request signing.

Exact ports from RedCrack encrypt module.
"""

from __future__ import annotations

import time
from urllib.parse import urlparse

from rednote_core.crypto.cookie.a1_webid import generate_a1, generate_web_id
from rednote_core.crypto.cookie.gid import build_gid_request
from rednote_core.crypto.cookie.websectiga import decode_websectiga
from rednote_core.crypto.header.x_b3 import generate_x_b3_traceid
from rednote_core.crypto.header.x_xray import generate_x_xray_traceid
from rednote_core.crypto.header.x_s_common import generate_x_s_common
from rednote_core.crypto.header.x_s import generate_x_s
from rednote_core.crypto.header.x_rap_param import generate_x_rap_param


def generate_cookies() -> dict[str, str]:
    """Generate locally-computable cookies: a1, webId.

    websectiga, gid, sec_poison_id, acw_tc all require API calls
    and are NOT generated here. They are obtained during session initialization.
    """
    a1 = generate_a1()
    return {
        "a1": a1,
        "webId": generate_web_id(a1),
    }


def sign_request(
    method: str,
    url: str,
    data: str | None,
    cookies: dict[str, str],
    headers: dict[str, str],
    fp: dict | None = None,
) -> dict[str, str]:
    """Sign an API request by generating all required security headers.

    This mirrors RedCrack XHS_Session.__request_encrypt.

    Args:
        fp: Full browser fingerprint dict (from XhsFpGenerator.get_fingerprint).
            If None, x-s-common uses a minimal placeholder.
    """
    a1 = cookies.get("a1", "")
    loadts_str = cookies.get("loadts", str(int(time.time())))
    loadts = int(loadts_str)

    parsed = urlparse(url)
    url_path = parsed.path
    if parsed.query:
        url_path = url_path + "?" + parsed.query

    # x-xray must come first (its internal seq depends on current ms)
    xray = generate_x_xray_traceid()

    # x-b3
    xb3 = generate_x_b3_traceid()

    # x-s (full RedCrack algorithm) — pass full path+query so the
    # signature covers query params like qr_id / code in status polling
    xs = generate_x_s(a1, loadts, url_path, params=None, data=data)

    # x-t
    xt = str(int(time.time() * 1000))

    # x-s-common
    xsc = generate_x_s_common(a1, loadts, url_path, fp=fp)

    # x-rap-param (only for certain URLs)
    result: dict[str, str] = {
        "x-s": xs,
        "x-s-common": xsc,
        "x-t": xt,
        "x-b3-traceid": xb3,
        "x-xray-traceid": xray,
    }

    xrap = generate_x_rap_param(url, data)
    if xrap is not None:
        result["x-rap-param"] = xrap

    return result


__all__ = [
    "generate_a1",
    "generate_web_id",
    "build_gid_request",
    "decode_websectiga",
    "generate_cookies",
    "sign_request",
    "generate_x_b3_traceid",
    "generate_x_xray_traceid",
    "generate_x_s",
    "generate_x_s_common",
    "generate_x_rap_param",
]
