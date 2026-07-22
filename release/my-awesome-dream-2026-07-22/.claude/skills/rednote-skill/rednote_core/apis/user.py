"""User info and user notes APIs."""

from rednote_core.client.session import XHSClient
from rednote_core.apis.models import UserInfo, UserNotesResult, NoteCard, UserBrief, InteractInfo
from rednote_core.client.exceptions import ParseError


async def get_user_info(
    client: XHSClient,
    target_user_id: str,
) -> UserInfo:
    """Get user profile information."""
    resp = await client.get(
        "/api/sns/web/v1/user/otherinfo",
        params={"target_user_id": target_user_id},
    )

    if resp.status_code != 200:
        raise ParseError(f"User info returned {resp.status_code}")

    data = resp.json()
    if not data.get("success"):
        raise ParseError(f"User info failed: {data.get('msg', 'unknown')}")

    user_data = data.get("data", {}).get("user", {})

    return UserInfo(
        user_id=target_user_id,
        nickname=user_data.get("nickname", ""),
        avatar=user_data.get("images", ""),
        red_id=user_data.get("red_id", ""),
        desc=user_data.get("desc", ""),
        gender=user_data.get("gender", 0),
        follows=int(user_data.get("follows", 0)),
        fans=int(user_data.get("fans", 0)),
        interaction=int(user_data.get("interaction", 0)),
        ip_location=user_data.get("ip_location", ""),
        tags=user_data.get("tags", []),
    )


async def get_user_notes(
    client: XHSClient,
    user_id: str,
    cursor: str = "",
    num: int = 30,
) -> UserNotesResult:
    """Get a user's posted notes."""
    resp = await client.get(
        "/api/sns/web/v1/user_posted",
        params={
            "user_id": user_id,
            "num": num,
            "cursor": cursor,
            "image_formats": "jpg,webp,avif",
            "xsec_source": "pc_feed",
        },
    )

    if resp.status_code != 200:
        raise ParseError(f"User notes returned {resp.status_code}")

    data = resp.json()
    if not data.get("success"):
        raise ParseError(f"User notes failed: {data.get('msg', 'unknown')}")

    raw_data = data.get("data", {})
    notes = []
    for nc in raw_data.get("notes", []):
        interact = nc.get("interact_info", {})
        user = nc.get("user", {})
        notes.append(NoteCard(
            note_id=nc.get("note_id", ""),
            title=nc.get("display_title", ""),
            desc=nc.get("desc", ""),
            type=nc.get("type", "normal"),
            xsec_token=nc.get("xsec_token", ""),
            user=UserBrief(
                user_id=user.get("user_id", ""),
                nickname=user.get("nickname", ""),
                avatar=user.get("avatar", ""),
            ) if user else None,
            interact_info=InteractInfo(
                liked_count=int(interact.get("liked_count", 0)),
                collected_count=int(interact.get("collected_count", 0)),
                comment_count=int(interact.get("comment_count", 0)),
                share_count=int(interact.get("share_count", 0)),
            ) if interact else None,
            time=int(nc.get("time", 0)),
            ip_location=nc.get("ip_location", ""),
        ))

    return UserNotesResult(
        notes=notes,
        has_more=raw_data.get("has_more", False),
        cursor=raw_data.get("cursor", ""),
    )
