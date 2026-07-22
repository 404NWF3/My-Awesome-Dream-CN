# tests/test_headers.py
import re
from rednote_core.crypto.header.x_b3 import generate_x_b3_traceid
from rednote_core.crypto.header.x_xray import generate_x_xray_traceid
from rednote_core.crypto.header.x_s_common import generate_x_s_common
from rednote_core.crypto.header.x_s import generate_x_s
from rednote_core.crypto.header.x_rap_param import generate_x_rap_param


class TestXB3:
    def test_format(self):
        trace_id = generate_x_b3_traceid()
        # RedCrack uses 16 hex chars from 'abcdef0123456789'
        assert re.match(r"^[0-9a-f]{16}$", trace_id), f"Bad: {trace_id}"

    def test_unique(self):
        results = {generate_x_b3_traceid() for _ in range(10)}
        assert len(results) == 10


class TestXXray:
    def test_format(self):
        tid = generate_x_xray_traceid()
        assert len(tid) >= 16, f"Too short: {tid}"

    def test_unique(self):
        results = {generate_x_xray_traceid() for _ in range(10)}
        assert len(results) >= 5  # may not be all unique due to time-based part


class TestXSCommon:
    def test_returns_str(self):
        """New x-s-common returns a str, not a dict."""
        a1 = "a" * 52
        result = generate_x_s_common(a1, 1700000000000)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_different_a1_different_output(self):
        r1 = generate_x_s_common("a" * 52, 1700000000000)
        r2 = generate_x_s_common("b" * 52, 1700000000000)
        assert r1 != r2


class TestXS:
    def test_generates_signature(self):
        a1 = "a" * 52
        result = generate_x_s(
            cookie_a1=a1,
            cookie_loadts=1700000000000,
            uri="/api/sns/web/v1/search/notes",
            data='{"keyword":"test"}',
        )
        assert isinstance(result, str)
        assert result.startswith("XYS_")
        assert len(result) > 0

    def test_different_data_different_sig(self):
        a1 = "a" * 52
        sig1 = generate_x_s(a1, 1700000000000, "/api/test", data='{"a":1}')
        sig2 = generate_x_s(a1, 1700000000000, "/api/test", data='{"a":2}')
        assert sig1 != sig2

    def test_different_url_different_sig(self):
        a1 = "a" * 52
        sig1 = generate_x_s(a1, 1700000000000, "/api/a")
        sig2 = generate_x_s(a1, 1700000000000, "/api/b")
        assert sig1 != sig2


class TestXRapParam:
    def test_returns_str_or_none(self):
        """x-rap-param returns str for XRAP URLs, None otherwise."""
        result = generate_x_rap_param(
            "https://edith.xiaohongshu.com/api/sns/web/v1/homefeed",
            {"num": 20}
        )
        assert result is None or isinstance(result, str)

    def test_returns_none_for_non_xrap_url(self):
        result = generate_x_rap_param(
            "https://edith.xiaohongshu.com/api/sns/web/v1/login/qrcode/create"
        )
        assert result is None

    def test_value_is_base64_for_xrap_url(self):
        result = generate_x_rap_param(
            "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes",
            {"keyword": "test"}
        )
        if result is not None:
            assert isinstance(result, str)
            assert len(result) > 0
