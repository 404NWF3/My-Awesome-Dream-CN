"""HTTP request helper that uses curl subprocess for edith.xiaohongshu.com.

Background: TencentEdgeOne CDN on edith.xiaohongshu.com fingerprints the
TLS handshake (JA3/JA4) and blocks httpx's TLS profile. curl's TLS profile
passes through successfully. This module wraps curl for edith requests.
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from typing import Any

from rednote_core.crypto import sign_request
from rednote_core.crypto.fingerprint import update_fingerprint

logger = logging.getLogger(__name__)


class CurlResponse:
    """Minimal response wrapper matching httpx.Response interface used by login_qrcode."""

    def __init__(self, status_code: int, headers: dict[str, str], body: str, cookies: dict[str, str]):
        self.status_code = status_code
        self.headers = headers
        self._body = body
        self._cookies = cookies

    @property
    def text(self) -> str:
        return self._body

    def json(self) -> Any:
        return json.loads(self._body)

    @property
    def cookies(self):
        return _CookieJar(self._cookies)


class _CookieJar:
    """Minimal cookie jar for compatibility."""

    def __init__(self, cookies: dict[str, str]):
        self._cookies = cookies

    @property
    def jar(self):
        return [_Cookie(k, v) for k, v in self._cookies.items()]


class _Cookie:
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value


async def curl_request(
    method: str,
    url: str,
    cookies: dict[str, str],
    fp: dict | None = None,
    json_data: dict | None = None,
    params: dict | None = None,
) -> CurlResponse:
    """Make an HTTP request via curl subprocess.

    Generates security headers using the same sign_request function,
    then sends via curl to bypass TLS fingerprinting by CDN.
    """
    import time

    # Build request body
    body_str = None
    if json_data is not None:
        body_str = json.dumps(json_data, separators=(",", ":"))

    # Update loadts
    cookies["loadts"] = str(int(time.time() * 1000))

    # Update fingerprint
    if fp:
        update_fingerprint(fp, cookies, url)

    # Generate security headers
    sign_headers = sign_request(method, url, body_str, cookies, {}, fp=fp)

    # Build cookie string
    cookie_str = "; ".join(
        f"{k}={v}" for k, v in cookies.items()
        if v and all(ord(c) < 128 for c in v)
    )

    # Build full URL with params
    full_url = url
    if params:
        from urllib.parse import urlencode
        full_url += "?" + urlencode(params)

    # Build curl command
    cmd = ["curl", "-s", "-D", "-", "--http1.1", "-X", method.upper(), full_url]

    # Add security headers
    for k, v in sign_headers.items():
        cmd.extend(["-H", f"{k}: {v}"])

    # Add standard headers
    cmd.extend(["-H", "accept: application/json, text/plain, */*"])
    cmd.extend(["-H", "accept-language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"])
    cmd.extend(["-H", "content-type: application/json;charset=UTF-8"])
    cmd.extend(["-H", "origin: https://www.xiaohongshu.com"])
    cmd.extend(["-H", "referer: https://www.xiaohongshu.com/"])
    cmd.extend(["-H", f"Cookie: {cookie_str}"])

    if body_str:
        cmd.extend(["-d", body_str])

    # Run curl in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: subprocess.run(
        cmd, capture_output=True, text=True, timeout=30
    ))

    output = result.stdout

    # Parse HTTP response (headers + body)
    # Format: "HTTP/1.1 200 OK\r\nHeader: Value\r\n\r\nBody"
    header_end = output.find("\r\n\r\n")
    if header_end == -1:
        # Try without \r\n
        header_end = output.find("\n\n")
        if header_end == -1:
            raise RuntimeError(f"Failed to parse curl response: {output[:200]}")
        header_section = output[:header_end]
        body = output[header_end + 2:]
        sep_len = 2
    else:
        header_section = output[:header_end]
        body = output[header_end + 4:]
        sep_len = 4

    # Parse status line
    lines = header_section.split("\r\n") if "\r\n" in header_section else header_section.split("\n")
    status_line = lines[0]
    # "HTTP/1.1 200 OK" → 200
    parts = status_line.split(" ", 2)
    status_code = int(parts[1]) if len(parts) >= 2 else 0

    # Parse headers
    resp_headers = {}
    resp_cookies = {}
    for line in lines[1:]:
        if ": " in line:
            key, val = line.split(": ", 1)
            resp_headers[key.lower()] = val
            # Parse set-cookie
            if key.lower() == "set-cookie":
                # "acw_tc=xxx;path=/;HttpOnly;Max-Age=1800"
                cookie_parts = val.split(";")[0].strip()
                if "=" in cookie_parts:
                    ck, cv = cookie_parts.split("=", 1)
                    resp_cookies[ck.strip()] = cv.strip()

    # Also check for web_session in set-cookie
    for line in lines[1:]:
        if ": " in line:
            key, val = line.split(": ", 1)
            if key.lower() == "set-cookie" and "web_session=" in val:
                for part in val.split(";"):
                    part = part.strip()
                    if part.startswith("web_session="):
                        resp_cookies["web_session"] = part.split("=", 1)[1]

    return CurlResponse(status_code, resp_headers, body, resp_cookies)
