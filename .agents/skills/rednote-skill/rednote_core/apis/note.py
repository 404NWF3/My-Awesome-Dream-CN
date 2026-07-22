"""Note detail API."""

from rednote_core.client.session import XHSClient
from rednote_core.apis.models import NoteDetail, UserBrief, InteractInfo
from rednote_core.client.exceptions import ParseError


async def get_note_detail(
    client: XHSClient,
    source_note_id: str,
    xsec_token: str,
) -> NoteDetail:
    """Get full note details."""
    payload = {
        "source_note_id": source_note_id,
        "xsec_token": xsec_token,
        "xsec_source": "pc_feed",
        "image_formats": ["jpg", "webp", "avif"],
        "extra": {"need_body_topic": "1"},
    }

    resp = await client.post("/api/sns/web/v1/feed", json_data=payload)

    if resp.status_code != 200:
        raise ParseError(f"Feed returned {resp.status_code}")

    data = resp.json()
    if not data.get("success"):
        raise ParseError(f"Feed failed: {data.get('msg', 'unknown')}")

    items = data.get("data", {}).get("items", [])
    if not items:
        raise ParseError("No note data returned")

    nc = items[0].get("note_card", {})
    interact = nc.get("interact_info", {})
    user = nc.get("user", {})

    # Extract image URLs from image_list[].info_list[].url (WB_DFT scene)
    image_urls = []
    for img in nc.get("image_list", []):
        for info in img.get("info_list", []):
            if info.get("image_scene") == "WB_DFT":
                image_urls.append(info.get("url", ""))
                break

    return NoteDetail(
        note_id=nc.get("note_id", ""),
        title=nc.get("title", ""),
        desc=nc.get("desc", ""),
        type=nc.get("type", "normal"),
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
        tag_list=[t.get("name", "") for t in nc.get("tag_list", [])],
        image_list=image_urls,
        time=int(nc.get("time", 0)),
        ip_location=nc.get("ip_location", ""),
        update_time=int(nc.get("update_time", 0)),
    )
