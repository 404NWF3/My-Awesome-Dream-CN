"""XHSClient — the main HTTP client for Xiaohongshu API.

Wraps aiohttp.ClientSession with automatic:
  - Cookie injection (via cookie_jar)
  - Request signing (6 security headers)
  - Retry on 429/461
  - Proxy support

Uses aiohttp instead of httpx to match RedCrack's TLS fingerprint (JA3/JA4),
which is required to pass CDN WAF checks on edith.xiaohongshu.com.

Session initialization mirrors RedCrack XHS_Session._initialize + __init_cookies:
  1. a1 + webId (local)
  2. base cookies (loadts, webBuild, xsecappid)
  3. POST /api/sec/v1/scripting → websectiga + sec_poison_id
  4. Fingerprint generation
  5. POST /api/sec/v1/shield/webprofile → gid
  6. POST /api/sns/web/v1/login/activate → visitor web_session (if no login session)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Optional
from urllib.parse import urlparse

import aiohttp

from rednote_core.client.exceptions import (
    AuthError,
    RateLimitError,
    SecurityChallenge,
)
from rednote_core.crypto.config import DEFAULT_HEADERS
from rednote_core.crypto import generate_cookies, sign_request
from rednote_core.crypto.cookie.websectiga import decode_websectiga
from rednote_core.crypto.cookie.gid import build_gid_request
from rednote_core.crypto.fingerprint import get_fingerprint, update_fingerprint

logger = logging.getLogger(__name__)

# Base URLs
EDITH_BASE = "https://edith.xiaohongshu.com"
API_BASE = "https://www.xiaohongshu.com"


class _AioResponse:
    """Wrapper around aiohttp.ClientResponse matching the interface login_qrcode expects."""

    def __init__(self, resp: aiohttp.ClientResponse, body: bytes, cookies: dict[str, str]):
        self.status_code = resp.status
        self._body = body
        self._headers = {k.lower(): v for k, v in resp.headers.items()}
        self._cookies = cookies

    @property
    def text(self) -> str:
        return self._body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self._body)

    @property
    def headers(self):
        return self._headers

    @property
    def cookies(self):
        return _CookieJar(self._cookies)


class _CookieJar:
    """Minimal cookie jar for compatibility with login_qrcode."""
    def __init__(self, cookies: dict[str, str]):
        self._cookies = cookies

    @property
    def jar(self):
        return [_Cookie(k, v) for k, v in self._cookies.items()]


class _Cookie:
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value


class XHSClient:
    """Async HTTP client for Xiaohongshu API.

    Uses aiohttp to match RedCrack's TLS fingerprint.

    Usage:
        client = await XHSClient.create(proxy="http://127.0.0.1:7890")
        resp = await client.get("/api/sns/web/v1/user/me")
    """

    def __init__(
        self,
        proxy: str,
        cookies: dict[str, str],
        *,
        timeout: float = 30.0,
        retry_interval: float = 5.0,
        request_interval: float = 2.0,
        fp: dict | None = None,
    ):
        self._cookies = dict(cookies)
        self._proxy = proxy
        self._request_interval = request_interval
        self._retry_interval = retry_interval
        self._fp = fp  # Full browser fingerprint (from XhsFpGenerator)
        self._ua = DEFAULT_HEADERS.get("user-agent", "")

        # Build aiohttp session — mirrors RedCrack XHS_Session._initialize
        effective_proxy = proxy if proxy and proxy.lower() != "none" else None
        self._connector = aiohttp.TCPConnector()
        self._timeout = aiohttp.ClientTimeout(total=timeout)

        # Initial headers (RedCrack: __init_headers)
        initial_headers = DEFAULT_HEADERS.copy()
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=self._timeout,
            headers=initial_headers,
            trust_env=True,
        )

        # Set initial cookies (RedCrack: __init_cookies)
        for key, value in self._cookies.items():
            self._session.cookie_jar.update_cookies({key: str(value)})

    @classmethod
    async def create(
        cls,
        proxy: str,
        *,
        timeout: float = 30.0,
        retry_interval: float = 5.0,
        request_interval: float = 2.0,
        web_session: str | None = None,
    ) -> "XHSClient":
        """Create and initialize a session — mirrors RedCrack create_xhs_session.

        Steps (matching RedCrack order):
          1. Generate a1 + webId + base cookies
          2. Get websectiga + sec_poison_id (POST /api/sec/v1/scripting)
          3. Generate full fingerprint (80+ fields)
          4. Get gid (POST /api/sec/v1/shield/webprofile) using full fingerprint
          5. Activate visitor web_session OR use provided web_session
        """
        cookies = generate_cookies()
        cookies["loadts"] = str(int(time.time()))
        cookies["webBuild"] = "6.12.3"
        cookies["xsecappid"] = "xhs-pc-web"
        cookies["abRequestId"] = str(uuid.uuid4())

        client = cls(
            proxy=proxy,
            cookies=cookies,
            timeout=timeout,
            retry_interval=retry_interval,
            request_interval=request_interval,
        )

        try:
            # Step 1: Get acw_tc via edith homepage (TencentEdgeOne anti-crawl token)
            # Required for search API to return results
            try:
                resp = await client.get("https://edith.xiaohongshu.com/")
                for name, value in resp._cookies.items():
                    client._cookies[name] = value
                client._update_session_cookies()
                logger.debug(f"acw_tc obtained: {'acw_tc' in client._cookies}")
            except Exception as e:
                logger.debug(f"Could not get acw_tc: {e}")

            # Step 2: scripting → websectiga + sec_poison_id
            await client._init_scripting()

            # Step 3: Generate FULL fingerprint (mirrors RedCrack XhsFpGenerator.get_fingerprint)
            cookies_dict = client._get_session_cookies()
            fp = get_fingerprint(cookies_dict, client._ua)
            client._fp = fp
            logger.debug("Full fingerprint generated")

            # Step 4: shield/webprofile → gid using full fingerprint
            try:
                await client._init_gid()
            except Exception as e:
                logger.warning(f"Could not get gid cookie (non-fatal): {e}")

            # Step 5: activate → visitor web_session (RedCrack: __set_web_session)
            if web_session:
                client._cookies["web_session"] = web_session
                client._session.cookie_jar.update_cookies({"web_session": web_session})
            else:
                try:
                    await client._init_activate()
                except Exception as e:
                    logger.warning(f"Could not activate session: {e}")

            logger.debug(f"Session initialized: cookies={list(client._cookies.keys())}")

        except Exception:
            await client.close()
            raise

        return client

    def _get_session_cookies(self) -> dict[str, str]:
        """Get cookies from aiohttp cookie jar merged with local dict."""
        result = dict(self._cookies)
        for c in self._session.cookie_jar:
            result[c.key] = c.value
        return result

    def _sync_cookies_from_jar(self) -> None:
        """Sync aiohttp cookie jar cookies back to local dict."""
        for c in self._session.cookie_jar:
            self._cookies[c.key] = c.value

    def _update_session_cookies(self) -> None:
        """Push local cookie dict into aiohttp cookie jar."""
        for key, value in self._cookies.items():
            if value and all(ord(ch) < 128 for ch in str(value)):
                self._session.cookie_jar.update_cookies({key: str(value)})

    async def _init_scripting(self) -> None:
        """POST /api/sec/v1/scripting → websectiga + sec_poison_id."""
        url = "https://as.xiaohongshu.com/api/sec/v1/scripting"
        data = {"callFrom": "web", "callback": "seccallback"}

        resp = await self.post(url, json_data=data)

        if resp.status_code == 200:
            body = resp.json()
            if body.get("data", {}).get("data"):
                try:
                    self._cookies["websectiga"] = decode_websectiga(body["data"]["data"])
                except Exception:
                    logger.debug("websectiga decode failed")
            if body.get("data", {}).get("secPoisonId"):
                self._cookies["sec_poison_id"] = body["data"]["secPoisonId"]

            # Sync cookies from response
            for name, value in resp._cookies.items():
                self._cookies[name] = value
            self._update_session_cookies()

    async def _init_gid(self) -> None:
        """POST /api/sec/v1/shield/webprofile → gid.

        Uses the full fingerprint (80+ fields) from XhsFpGenerator.
        RedCrack: XHS_Gid_Webprofile_Data_Encrypt.gen_gid_webprofile_data(fp)
        """
        if not self._fp:
            logger.warning("No fingerprint available — skipping gid")
            return

        url, data = build_gid_request(self._fp)
        resp = await self.post(url, json_data=data)

        if resp.status_code == 200:
            for name, value in resp._cookies.items():
                self._cookies[name] = value
            self._update_session_cookies()

    async def _init_activate(self) -> None:
        """POST /api/sns/web/v1/login/activate → visitor web_session."""
        url = "https://edith.xiaohongshu.com/api/sns/web/v1/login/activate"
        resp = await self.post(url, json_data={})

        if resp.status_code == 200:
            for name, value in resp._cookies.items():
                self._cookies[name] = value
            self._update_session_cookies()

    @property
    def cookies(self) -> dict[str, str]:
        """Current cookies (read-only view)."""
        return dict(self._cookies)

    def update_cookies(self, new_cookies: dict[str, str]) -> None:
        """Merge new cookies into the current set."""
        self._cookies.update(new_cookies)
        self._update_session_cookies()

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> _AioResponse:
        """Make an HTTP request — mirrors RedCrack XHS_Session.request.

        Handles: cookie sync, security header injection, retry on errors.
        """
        # Resolve relative URLs
        # API endpoints (/api/*) go to edith.xiaohongshu.com
        # Non-API pages go to www.xiaohongshu.com
        if not url.startswith("http"):
            base = EDITH_BASE if url.startswith("/api/") else API_BASE
            url = f"{base}{url}" if url.startswith("/") else f"{base}/{url}"

        # Rate limiting
        await asyncio.sleep(self._request_interval)

        # Prepare request body (RedCrack: manual JSON serialization)
        request_data = None
        if json_data is not None:
            request_data = json.dumps(json_data, separators=(",", ":"))

        # Retry loop (mirrors RedCrack request method)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Update loadts + fingerprint BEFORE each request
                # (mirrors RedCrack __request_encrypt)
                loadts = str(int(time.time() * 1000))
                self._cookies["loadts"] = loadts
                self._update_session_cookies()

                if self._fp:
                    update_fingerprint(self._fp, self._cookies, url)

                # Generate security headers (mirrors RedCrack __request_encrypt)
                a1 = self._cookies.get("a1", "")
                parsed = urlparse(url)
                url_path = parsed.path
                if parsed.query:
                    url_path = url_path + "?" + parsed.query

                xs = sign_request.__wrapped__ if hasattr(sign_request, '__wrapped__') else None
                # Use sign_request for all headers
                extra = sign_request(
                    method=method, url=url, data=request_data,
                    cookies=self._cookies, headers={}, fp=self._fp,
                )

                # Update session headers with security headers
                for key, value in extra.items():
                    self._session.headers[key] = value

                # Build kwargs for aiohttp
                aio_kwargs: dict[str, Any] = {"params": params}
                if request_data is not None:
                    aio_kwargs["data"] = request_data
                elif data is not None:
                    aio_kwargs["data"] = data

                # Make the request
                async with self._session.request(
                    method, url, **aio_kwargs
                ) as resp:
                    body = await resp.read()

                    # Extract response cookies
                    resp_cookies = {}
                    for c in resp.cookies.values():
                        resp_cookies[c.key] = c.value
                    # Also check set-cookie headers
                    for hdr_name, hdr_val in resp.headers.items():
                        if hdr_name.lower() == "set-cookie":
                            for part in hdr_val.split(";"):
                                part = part.strip()
                                if "=" in part:
                                    k, v = part.split("=", 1)
                                    k = k.strip()
                                    if not k.startswith("_") and k.lower() in ("web_session", "sec_poison_id", "acw_tc", "gid"):
                                        resp_cookies[k] = v.strip()

                    response = _AioResponse(resp, body, resp_cookies)

                # Handle status codes (mirrors RedCrack __handle_xhs_response_exceptions)
                if response.status_code == 200:
                    return response

                if response.status_code in (461, 471):
                    if attempt < max_retries - 1:
                        logger.warning(f"Security challenge {response.status_code}, retrying...")
                        continue
                    raise SecurityChallenge(f"Security challenge on {url}")

                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        delay = self._retry_interval * (2 ** attempt)
                        logger.warning(f"Rate limited, waiting {delay:.0f}s (attempt {attempt + 1})")
                        await asyncio.sleep(delay)
                        continue
                    raise RateLimitError(f"Rate limited after {max_retries} retries")

                if response.status_code in (401, 403):
                    raise AuthError(f"Auth failed ({response.status_code})")

                return response

            except aiohttp.ClientError as e:
                if attempt < max_retries - 1:
                    delay = self._retry_interval * (2 ** attempt)
                    logger.warning(f"Request error: {e} — retrying in {delay:.0f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    continue
                raise

        raise RateLimitError("Max retries exceeded")

    async def get(
        self, url: str, *, params: Optional[dict] = None, **kwargs
    ) -> _AioResponse:
        return await self.request("GET", url, params=params, **kwargs)

    async def post(
        self,
        url: str,
        *,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        data: Optional[dict] = None,
        **kwargs,
    ) -> _AioResponse:
        return await self.request(
            "POST", url, params=params, json_data=json_data, data=data, **kwargs
        )

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
        if self._connector:
            await self._connector.close()
            self._connector = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
