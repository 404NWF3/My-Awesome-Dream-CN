# tests/test_apis.py
"""API endpoint unit tests with mocked HTTP."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from rednote_core.apis.models import SearchResult, NoteCard, NoteDetail, UserInfo
from rednote_core.apis.search import search_notes, _generate_search_id
from rednote_core.apis.note import get_note_detail
from rednote_core.apis.user import get_user_info


class TestSearchId:
    def test_generates_valid_base36(self):
        sid = _generate_search_id()
        assert len(sid) > 0
        assert all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in sid)


class TestSearchNotes:
    @pytest.mark.asyncio
    async def test_parses_search_response(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "has_more": False,
                "cursor": "",
                "items": [
                    {
                        "id": "12345",
                        "xsec_token": "xsec_abc",
                        "model_type": "note",
                        "note_card": {
                            "display_title": "Test Note",
                            "desc": "Test desc",
                            "type": "normal",
                            "user": {
                                "user_id": "u1",
                                "nickname": "Tester",
                                "avatar": "http://img.url",
                            },
                            "interact_info": {
                                "liked_count": "100",
                                "collected_count": "50",
                                "comment_count": "10",
                                "share_count": "5",
                            },
                            "tag_list": [{"name": "tag1"}],
                            "image_list": [{"url": "http://img1"}],
                            "time": 1700000000,
                            "ip_location": "上海",
                        }
                    }
                ],
            },
        }
        mock_client.post = AsyncMock(return_value=mock_response)

        result = await search_notes(mock_client, keyword="test")

        assert isinstance(result, SearchResult)
        assert len(result.items) == 1
        assert result.items[0].note_id == "12345"
        assert result.items[0].title == "Test Note"
        assert result.items[0].interact_info.liked_count == 100

    @pytest.mark.asyncio
    async def test_search_failure_raises(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": False, "msg": "error"}
        mock_client.post = AsyncMock(return_value=mock_response)

        from rednote_core.client.exceptions import ParseError
        with pytest.raises(ParseError):
            await search_notes(mock_client, keyword="test")


class TestNoteDetail:
    @pytest.mark.asyncio
    async def test_parses_feed_response(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "items": [
                    {
                        "note_card": {
                            "note_id": "12345",
                            "title": "Full Note",
                            "desc": "Full body",
                            "type": "normal",
                            "user": {"user_id": "u1", "nickname": "Author", "avatar": ""},
                            "interact_info": {
                                "liked_count": "200",
                                "collected_count": "100",
                                "comment_count": "30",
                                "share_count": "10",
                            },
                            "tag_list": [],
                            "image_list": [],
                            "time": 1700000000,
                            "ip_location": "北京",
                            "update_time": 1700000100,
                        }
                    }
                ]
            },
        }
        mock_client.post = AsyncMock(return_value=mock_response)

        result = await get_note_detail(mock_client, "12345", "xsec_abc")

        assert isinstance(result, NoteDetail)
        assert result.note_id == "12345"
        assert result.title == "Full Note"
        assert result.interact_info.liked_count == 200


class TestUserInfo:
    @pytest.mark.asyncio
    async def test_parses_user_response(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "user": {
                    "nickname": "TestUser",
                    "images": "http://avatar",
                    "red_id": "1234567",
                    "desc": "Bio here",
                    "gender": 1,
                    "follows": "100",
                    "fans": "1000",
                    "interaction": "5000",
                    "ip_location": "杭州",
                    "tags": ["美妆", "护肤"],
                }
            },
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await get_user_info(mock_client, "target_uid")

        assert isinstance(result, UserInfo)
        assert result.nickname == "TestUser"
        assert result.fans == 1000
        assert "美妆" in result.tags
