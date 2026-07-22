"""Homefeed / recommend API."""

from rednote_core.client.session import XHSClient
from rednote_core.apis.models import HomefeedResult, NoteCard, UserBrief, InteractInfo
from rednote_core.client.exceptions import ParseError

CATEGORIES = {
    "recommend": "homefeed_recommend",
    "fashion": "homefeed.fashion_v3",
    "food": "homefeed.food_v3",
    "cosmetics": "homefeed.cosmetics_v3",
    "movie": "homefeed.movie_and_tv_v3",
    "career": "homefeed.career_v3",
    "love": "homefeed.love_v3",
    "household": "homefeed.household_product_v3",
    "gaming": "homefeed.gaming_v3",
    "travel": "homefeed.travel_v3",
    "fitness": "homefeed.fitness_v3",
}


async def get_homefeed(
    client: XHSClient,
    category: str = "recommend",
    cursor_score: str = "",
    num: int = 25,
) -> HomefeedResult:
    """Get homefeed / category recommend notes."""
    api_category = CATEGORIES.get(category, category)

    payload = {
        "category": api_category,
        "cursor_score": cursor_score,
        "note_index": 0,
        "num": num,
        "refresh_type": 1,
        "need_num": 10,
        "image_formats": ["jpg", "webp", "avif"],
    }

    resp = await client.post("/api/sns/web/v1/homefeed", json_data=payload)

    if resp.status_code != 200:
        raise ParseError(f"Homefeed returned {resp.status_code}")

    data = resp.json()
    if not data.get("success"):
        raise ParseError(f"Homefeed failed: {data.get('msg', 'unknown')}")

    raw_data = data.get("data", {})
    items = []
    for item in raw_data.get("items", []):
        nc = item.get("note_card", {})
        if nc:
            interact = nc.get("interact_info", {})
            user = nc.get("user", {})
            items.append(NoteCard(
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

    return HomefeedResult(
        items=items,
        has_more=raw_data.get("has_more", False),
        cursor_score=raw_data.get("cursor_score", ""),
    )
