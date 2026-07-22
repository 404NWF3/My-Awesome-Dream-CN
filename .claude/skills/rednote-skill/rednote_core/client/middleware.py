"""HTTP middleware for automatic request signing and retry logic.

NOTE: This module is currently UNUSED — session.py implements signing
and retry logic directly with aiohttp. Kept for reference.
"""

from __future__ import annotations

import time
import logging
import typing
from typing import Optional, Any

from rednote_core.crypto import sign_request
from rednote_core.crypto.fingerprint import update_fingerprint
from rednote_core.client.exceptions import (
    CryptoError,
    AuthError,
    RateLimitError,
    SecurityChallenge,
)

logger = logging.getLogger(__name__)


class RequestSigner:
    """Middleware that injects Xiaohongshu security headers into requests.

    This is the core middleware — every request passes through it
    to have x-s, x-s-common, x-t, x-b3-traceid, x-xray-traceid,
    and x-rap-param injected automatically.

    IMPORTANT: mirrors RedCrack XHS_Session.__request_encrypt which
    updates loadts cookie AND fingerprint before EVERY request.
    """

    def __init__(self, cookies: dict[str, str], fp: dict | None = None):
        self._cookies = cookies
        self._fp = fp

    def sign(
        self, method: str, url: str, body: bytes | None, headers: dict[str, str]
    ) -> dict[str, str]:
        """Generate signature headers for a request."""
        import time as _time

        try:
            loadts = str(int(_time.time() * 1000))
            self._cookies["loadts"] = loadts

            if self._fp:
                update_fingerprint(self._fp, self._cookies, url)

            body_str = None
            if body:
                body_str = body.decode("utf-8", errors="replace")

            extra_headers = sign_request(
                method=method,
                url=url,
                data=body_str,
                cookies=self._cookies,
                headers=headers,
                fp=self._fp,
            )
            return extra_headers

        except Exception as e:
            raise CryptoError(f"Failed to sign request: {e}") from e


class RetryMiddleware:
    """Retry handler for 429 and 461 responses."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 5.0,
        on_461=None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.on_461 = on_461

    async def __call__(
        self,
        request: Any,
        next_handler,
    ) -> Any:
        for attempt in range(self.max_retries + 1):
            try:
                response = await next_handler(request)
            except Exception as e:
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        f"Transport error: {e} — retrying in {delay:.0f}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(delay)
                    continue
                raise

            if response.status_code == 200:
                return response

            if response.status_code == 461:
                if self.on_461 and attempt == 0:
                    logger.warning("461 security challenge, refreshing...")
                    self.on_461()
                    continue
                raise SecurityChallenge(
                    f"Security challenge"
                )

            if response.status_code == 429:
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        f"Rate limited, waiting {delay:.0f}s (attempt {attempt + 1})"
                    )
                    time.sleep(delay)
                    continue
                raise RateLimitError(
                    f"Rate limited after {self.max_retries} retries"
                )

            if response.status_code in (401, 403):
                raise AuthError(
                    f"Auth failed ({response.status_code}) — re-run `rednote login`"
                )

            return response

        raise RateLimitError("Max retries exceeded")
