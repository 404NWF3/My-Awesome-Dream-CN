"""Search notes API."""

import time
import random
from rednote_core.client.session import XHSClient
from rednote_core.apis.models import SearchResult, NoteCard, UserBrief, InteractInfo
from rednote_core.client.exceptions import ParseError


def _base36encode(number: int, alphabet: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") -> str:
    """Encode integer to base36 — exact port of RedCrack base36encode."""
    if not isinstance(number, int):
        raise TypeError("number must be an integer")
    base36 = ""
    sign = ""
    if number < 0:
        sign = "-"
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36


def _generate_search_id() -> str:
    """Generate search_id — exact port of RedCrack get_search_id.

    Format: base36encode((timestamp_ms << 64) + random_int)
    Uses UPPERCASE alphabet (0-9A-Z).
    """
    e = int(time.time() * 1000) << 64
    t = int(random.uniform(0, 2147483646))
    return _base36encode(e + t)


async def search_notes(
    client: XHSClient,
    *,
    keyword: str,
    page: int = 1,
    page_size: int = 20,
    sort: str = "general",
    note_type: int = 0,
) -> SearchResult:
    """Search for notes by keyword."""
    search_id = _generate_search_id()

    payload = {
        "keyword": keyword,
        "page": page + 1,
        "page_size": min(page_size, 20),
        "sort": sort,
        "note_type": note_type,
        "search_id": search_id,
        "image_formats": ["jpg", "webp", "avif"],
        "ext_flags": [],
        "geo": "",
    }

    resp = await client.post(
        "/api/sns/web/v1/search/notes",
        json_data=payload,
    )

    if resp.status_code != 200:
        raise ParseError(f"Search returned {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    if not data.get("success", False):
        raise ParseError(f"Search failed: {data.get('msg', 'unknown')}")

    items = []
    raw_items = data.get("data", {}).get("items", [])
    for item in raw_items:
        nc = item.get("note_card", {})
        if nc:
            # note_id and xsec_token are at item level, not inside note_card
            note_id = item.get("id", "")
            xsec_token = item.get("xsec_token", "")
            card = _parse_note_card(nc)
            card.note_id = note_id
            card.xsec_token = xsec_token
            items.append(card)

    return SearchResult(
        items=items,
        has_more=data.get("data", {}).get("has_more", False),
        cursor=data.get("data", {}).get("cursor", ""),
    )


def _parse_note_card(nc: dict) -> NoteCard:
    interact = nc.get("interact_info", {})
    user = nc.get("user", {})

    # Extract image URLs from image_list[].info_list[].url (WB_DFT scene)
    image_urls = []
    for img in nc.get("image_list", []):
        for info in img.get("info_list", []):
            if info.get("image_scene") == "WB_DFT":
                image_urls.append(info.get("url", ""))
                break

    # Extract cover URL
    cover = nc.get("cover", {})
    cover_url = cover.get("url_default", "") or cover.get("url_pre", "")

    return NoteCard(
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
        tag_list=[t.get("name", "") for t in nc.get("tag_list", [])],
        image_list=image_urls,
        cover_url=cover_url,
        time=int(nc.get("time", 0)),
        ip_location=nc.get("ip_location", ""),
    )
