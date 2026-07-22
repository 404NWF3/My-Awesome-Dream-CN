"""Comment APIs."""

from rednote_core.client.session import XHSClient
from rednote_core.apis.models import CommentResult, Comment
from rednote_core.client.exceptions import ParseError


async def get_comments(
    client: XHSClient,
    note_id: str,
    xsec_token: str,
    cursor: str = "",
) -> CommentResult:
    """Get comments for a note."""
    resp = await client.get(
        "/api/sns/web/v2/comment/page",
        params={
            "note_id": note_id,
            "xsec_token": xsec_token,
            "cursor": cursor,
            "top_comment_id": "",
            "image_formats": "jpg,webp,avif",
        },
    )

    if resp.status_code != 200:
        raise ParseError(f"Comments returned {resp.status_code}")

    data = resp.json()
    if not data.get("success"):
        raise ParseError(f"Comments failed: {data.get('msg', 'unknown')}")

    raw_data = data.get("data", {})
    comments = []
    for c in raw_data.get("comments", []):
        user_info = c.get("user_info", {})
        comments.append(Comment(
            comment_id=c.get("id", ""),
            content=c.get("content", ""),
            user_id=user_info.get("user_id", ""),
            user_nickname=user_info.get("nickname", ""),
            user_avatar=user_info.get("image", ""),
            like_count=int(c.get("like_count", 0)),
            sub_comment_count=int(c.get("sub_comment_count", 0)),
            create_time=int(c.get("create_time", 0)),
            ip_location=c.get("ip_location", ""),
        ))

    return CommentResult(
        comments=comments,
        has_more=raw_data.get("has_more", False),
        cursor=raw_data.get("cursor", ""),
    )


async def get_sub_comments(
    client: XHSClient,
    note_id: str,
    root_comment_id: str,
    cursor: str = "",
) -> CommentResult:
    """Get sub-comments (replies) for a comment."""
    resp = await client.get(
        "/api/sns/web/v2/comment/sub/page",
        params={
            "note_id": note_id,
            "root_comment_id": root_comment_id,
            "num": 30,
            "cursor": cursor,
        },
    )

    if resp.status_code != 200:
        raise ParseError(f"Sub comments returned {resp.status_code}")

    data = resp.json()
    if not data.get("success"):
        raise ParseError(f"Sub comments failed: {data.get('msg', 'unknown')}")

    raw_data = data.get("data", {})
    comments = []
    for c in raw_data.get("comments", []):
        user_info = c.get("user_info", {})
        comments.append(Comment(
            comment_id=c.get("id", ""),
            content=c.get("content", ""),
            user_id=user_info.get("user_id", ""),
            user_nickname=user_info.get("nickname", ""),
            user_avatar=user_info.get("image", ""),
            like_count=int(c.get("like_count", 0)),
            create_time=int(c.get("create_time", 0)),
            ip_location=c.get("ip_location", ""),
        ))

    return CommentResult(
        comments=comments,
        has_more=raw_data.get("has_more", False),
        cursor=raw_data.get("cursor", ""),
    )
