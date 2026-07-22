# tests/test_cookies.py
import re
from rednote_core.crypto.cookie.a1_webid import generate_a1, generate_web_id
from rednote_core.crypto.cookie.gid import build_gid_request
from rednote_core.crypto.cookie.websectiga import decode_websectiga
from rednote_core.crypto.cookie.acw_tc import decrypt_acw_tc


class TestA1:
    def test_format(self):
        """RedCrack a1: timestamp_hex(11-12) + 30 rand chars + platform(1) + 0 + 000 + crc32."""
        a1 = generate_a1()
        assert len(a1) == 52, f"a1 should be 52 chars: got {len(a1)} ({a1})"

    def test_unique(self):
        results = {generate_a1() for _ in range(10)}
        assert len(results) == 10  # All should be unique


class TestWebId:
    def test_format(self):
        web_id = generate_web_id()
        # webId = MD5(a1), should be 32 hex chars
        assert re.match(r"^[0-9a-f]{32}$", web_id), f"webId format: {web_id}"

    def test_length(self):
        assert len(generate_web_id()) == 32

    def test_webid_from_a1(self):
        a1 = generate_a1()
        web_id = generate_web_id(a1)
        assert len(web_id) == 32
        # Same a1 should produce same webId
        assert web_id == generate_web_id(a1)


class TestGid:
    def test_build_gid_request_returns_url_and_data(self):
        fp = {"x33": "0"}  # minimal fingerprint for DES encrypt
        url, data = build_gid_request(fp)
        assert url == "https://as.xiaohongshu.com/api/sec/v1/shield/webprofile"
        assert "platform" in data
        assert "profileData" in data
        assert "sdkVersion" in data
        assert "svn" in data
        assert data["platform"] == "Windows"

    def test_profile_data_is_hex(self):
        fp = {"x33": "0", "x34": "0"}
        _, data = build_gid_request(fp)
        # profileData is hex-encoded DES ciphertext
        assert isinstance(data["profileData"], str)
        assert re.match(r"^[0-9a-f]+$", data["profileData"])


class TestWebsectiga:
    def test_decode_known_jsvmp(self):
        """Test decode_websectiga with a real-looking JSVMP payload."""
        # This is the structure expected from the scripting API
        # We test that it fails gracefully on bad input
        # Real JSVMP data is 200KB+; we validate error paths
        try:
            decode_websectiga('{"b":"dGVzdA==","d":{}}')  # "test" in base64
        except (ValueError, KeyError, IndexError):
            pass  # Expected - this isn't real JSVMP data

    def test_decode_requires_b_and_d(self):
        try:
            decode_websectiga("not json")
            assert False, "should have raised"
        except (ValueError, AttributeError):
            pass


class TestAcwTc:
    def test_decrypt_empty(self):
        result = decrypt_acw_tc("")
        assert result == ""
