# tests/test_middleware.py
"""Tests for request signing — verifies security headers are generated correctly."""

import pytest
from rednote_core.crypto import sign_request
from rednote_core.crypto.fingerprint import get_fingerprint, update_fingerprint


class TestSignRequest:
    def test_generates_all_security_headers(self):
        cookies = {
            "a1": "a" * 32,
            "web_session": "test_session",
            "webId": "b" * 32,
            "gid": "c" * 16,
            "websectiga": "d" * 32,
            "loadts": "1700000000000",
        }
        headers = sign_request(
            method="GET",
            url="https://edith.xiaohongshu.com/api/sns/web/v1/test",
            data=None,
            cookies=cookies,
            headers={},
        )

        assert "x-s" in headers
        assert "x-s-common" in headers
        assert "x-t" in headers
        assert "x-b3-traceid" in headers
        assert "x-xray-traceid" in headers

    def test_different_urls_different_signatures(self):
        cookies = {"a1": "a" * 32, "web_session": "", "loadts": "1700000000000"}

        h1 = sign_request("GET", "https://edith.xiaohongshu.com/api/a", None, cookies, {})
        h2 = sign_request("GET", "https://edith.xiaohongshu.com/api/b", None, cookies, {})

        assert h1["x-s"] != h2["x-s"]

    def test_with_fingerprint(self):
        cookies = {"a1": "a" * 32, "web_session": "", "loadts": "1700000000000"}
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        fp = get_fingerprint(cookies, ua)

        h1 = sign_request("GET", "https://edith.xiaohongshu.com/api/test", None, cookies, {}, fp=fp)
        h2 = sign_request("GET", "https://edith.xiaohongshu.com/api/test", None, cookies, {}, fp=None)

        # x-s-common should differ when fingerprint is provided
        assert h1["x-s-common"] != h2["x-s-common"]
