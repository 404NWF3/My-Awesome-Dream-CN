# tests/test_integration.py
"""Integration smoke tests — verify full stack imports and basic functionality."""

import pytest


class TestImports:
    """Verify all modules import correctly."""

    def test_import_crypto(self):
        from rednote_core.crypto import generate_cookies, sign_request
        assert callable(generate_cookies)
        assert callable(sign_request)

    def test_import_client(self):
        from rednote_core.client import XHSClient, AuthError, RedNoteError
        assert XHSClient is not None

    def test_import_apis(self):
        from rednote_core.apis import (
            search_notes, get_note_detail, get_user_info,
            get_user_notes, get_comments, get_homefeed,
        )
        assert callable(search_notes)

    def test_import_auth(self):
        from rednote_core.auth import login_qrcode, check_login, load_cookies
        assert callable(login_qrcode)

    def test_import_report(self):
        from rednote_core.report import render_report, render_search_report
        assert callable(render_report)

    def test_import_config(self):
        from rednote_core.config import load_config
        config = load_config()
        assert "client" in config
        assert "proxy" in config["client"]

    def test_generate_cookies_has_all_keys(self):
        from rednote_core.crypto import generate_cookies
        cookies = generate_cookies()
        assert "a1" in cookies
        assert "webId" in cookies
        # gid and websectiga are now obtained from API calls, not local generation

    def test_sign_request_returns_headers(self):
        from rednote_core.crypto import sign_request
        headers = sign_request(
            "GET", "https://edith.xiaohongshu.com/api/test",
            None,
            {"a1": "a" * 32, "web_session": ""},
            {},
        )
        assert "x-s" in headers
        assert "x-t" in headers
        assert "x-b3-traceid" in headers

    def test_cli_app_imports(self):
        from rednote.__main__ import app
        assert app is not None

    def test_report_render(self):
        from rednote_core.report import render_report
        html = render_report("base.html", {"generated_at": "2026-01-01"})
        assert "RedNote Report" in html
        assert "2026-01-01" in html


class TestConfig:
    def test_load_default_config(self):
        from rednote_core.config import load_config
        config = load_config()
        assert config["client"]["proxy"].lower() == "none"
        assert config["client"]["timeout"] == 30
        assert config["auth"]["cookies_file"] == "config/cookies.enc"


class TestModels:
    def test_create_models(self):
        from rednote_core.apis.models import (
            NoteCard, UserInfo, Comment, SearchResult,
            InteractInfo, UserBrief, CommentResult, HomefeedResult,
        )
        card = NoteCard(note_id="123", title="Test")
        assert card.note_id == "123"

        user = UserInfo(user_id="u1", nickname="Test", fans=100)
        assert user.fans == 100

        result = SearchResult(items=[card], has_more=True)
        assert len(result.items) == 1
        assert result.has_more
