"""Scrape commands — data collection from Xiaohongshu."""

from __future__ import annotations

import asyncio
import json
import typer
from rednote_core.crypto import generate_cookies
from rednote_core.client import XHSClient
from rednote_core.auth import load_cookies
from rednote_core.config import load_config
from rednote_core.apis import (
    search_notes,
    get_note_detail,
    get_user_info,
    get_user_notes,
    get_comments,
    get_homefeed,
)

scrape_app = typer.Typer(help="数据采集", no_args_is_help=True)


async def _get_client() -> XHSClient:
    """Create a fully initialized XHSClient with saved login cookies.

    Uses XHSClient.create() to run full session init (scripting + fingerprint + gid),
    then passes saved web_session for authenticated access.
    """
    config = load_config()
    saved = load_cookies(config["auth"]["cookies_file"])

    return await XHSClient.create(
        proxy=config["client"]["proxy"],
        timeout=config["client"]["timeout"],
        retry_interval=config["client"]["retry_interval"],
        request_interval=config["client"]["request_interval"],
        web_session=saved.get("web_session"),
    )


@scrape_app.command("search")
def search(
    keyword: str = typer.Option(..., "-k", "--keyword", help="搜索关键词"),
    count: int = typer.Option(20, "-n", "--count", help="返回条数"),
    sort: str = typer.Option("general", "-s", "--sort", help="排序: general/time_descending/popularity_descending"),
    note_type: str = typer.Option("all", "-t", "--type", help="类型: all/image/video"),
    format: str = typer.Option("json", "-f", "--format", help="输出格式: json/html"),
):
    """搜索笔记."""

    async def _run():
        client = await _get_client()
        try:
            type_map = {"all": 0, "image": 1, "video": 2}
            result = await search_notes(
                client,
                keyword=keyword,
                page_size=max(count, 20),  # server requires page_size >= 20
                sort=sort,
                note_type=type_map.get(note_type, 0),
            )

            if format == "json":
                items = []
                for item in result.items:
                    items.append({
                        "note_id": item.note_id,
                        "title": item.title,
                        "desc": item.desc[:100] if item.desc else "",
                        "type": item.type,
                        "author": item.user.nickname if item.user else "",
                        "author_id": item.user.user_id if item.user else "",
                        "likes": item.interact_info.liked_count if item.interact_info else 0,
                        "xsec_token": item.xsec_token,
                        "cover_url": item.cover_url,
                        "image_list": item.image_list,
                        "ip_location": item.ip_location,
                    })
                print(json.dumps(items, ensure_ascii=False, indent=2))
            else:
                for item in result.items:
                    print(f"📝 {item.title}")
                    print(f"   ID: {item.note_id} | 作者: {item.user.nickname if item.user else 'N/A'}")
                    print(f"   ❤️ {item.interact_info.liked_count if item.interact_info else 0} "
                          f"⭐ {item.interact_info.collected_count if item.interact_info else 0} "
                          f"💬 {item.interact_info.comment_count if item.interact_info else 0}")
                    if item.cover_url:
                        print(f"   🖼️ 封面: {item.cover_url}")
                    if item.image_list:
                        print(f"   📸 图片 ({len(item.image_list)}张): {item.image_list[0]}")
                    print()

            print(f"\n共 {len(result.items)} 条结果 (has_more={result.has_more})")
        finally:
            await client.close()

    asyncio.run(_run())


@scrape_app.command("note")
def note(
    note_id: str = typer.Argument(..., help="笔记 ID"),
    xsec_token: str = typer.Option("", "--xsec", help="xsec_token（从搜索结果获取）"),
):
    """获取笔记详情."""

    async def _run():
        client = await _get_client()
        try:
            detail = await get_note_detail(client, note_id, xsec_token)
            print(f"📝 {detail.title}")
            print(f"作者: {detail.user.nickname if detail.user else 'N/A'}")
            print(f"正文: {detail.desc[:200]}...")
            print(f"❤️ {detail.interact_info.liked_count if detail.interact_info else 0} "
                  f"⭐ {detail.interact_info.collected_count if detail.interact_info else 0} "
                  f"💬 {detail.interact_info.comment_count if detail.interact_info else 0}")
            print(f"标签: {', '.join(detail.tag_list)}")
            print(f"IP: {detail.ip_location} | 时间: {detail.time}")
            if detail.image_list:
                print(f"📸 图片 ({len(detail.image_list)}张):")
                for i, url in enumerate(detail.image_list):
                    print(f"   [{i+1}] {url}")
        finally:
            await client.close()

    asyncio.run(_run())


@scrape_app.command("user")
def user(
    user_id: str = typer.Argument(..., help="用户 ID"),
):
    """获取用户信息."""

    async def _run():
        client = await _get_client()
        try:
            info = await get_user_info(client, user_id)
            print(f"👤 {info.nickname} (@{info.red_id})")
            print(f"简介: {info.desc}")
            print(f"关注: {info.follows} | 粉丝: {info.fans} | 获赞与收藏: {info.interaction}")
            print(f"IP: {info.ip_location}")
            if info.tags:
                print(f"标签: {', '.join(info.tags)}")
        finally:
            await client.close()

    asyncio.run(_run())


@scrape_app.command("user-notes")
def user_notes(
    user_id: str = typer.Argument(..., help="用户 ID"),
    count: int = typer.Option(30, "-n", "--count", help="获取条数"),
):
    """获取用户笔记列表."""

    async def _run():
        client = await _get_client()
        try:
            result = await get_user_notes(client, user_id, num=count)
            for note in result.notes:
                print(f"📝 {note.title}")
                print(f"   ID: {note.note_id} | ❤️ {note.interact_info.liked_count if note.interact_info else 0}")
            print(f"\n共 {len(result.notes)} 条 (has_more={result.has_more})")
        finally:
            await client.close()

    asyncio.run(_run())


@scrape_app.command("comments")
def comments(
    note_id: str = typer.Argument(..., help="笔记 ID"),
    xsec_token: str = typer.Option("", "--xsec", help="xsec_token"),
):
    """获取笔记评论."""

    async def _run():
        client = await _get_client()
        try:
            result = await get_comments(client, note_id, xsec_token)
            for c in result.comments:
                print(f"💬 {c.user_nickname}: {c.content[:80]}")
                print(f"   👍 {c.like_count} | 回复: {c.sub_comment_count}")
            print(f"\n共 {len(result.comments)} 条评论 (has_more={result.has_more})")
        finally:
            await client.close()

    asyncio.run(_run())


@scrape_app.command("homefeed")
def homefeed(
    category: str = typer.Option("recommend", "-c", "--category", help="品类"),
    count: int = typer.Option(25, "-n", "--count", help="获取条数"),
):
    """获取推荐页（按品类）.

    品类: recommend, fashion, food, cosmetics, movie, career, love, household, gaming, travel, fitness
    """

    async def _run():
        client = await _get_client()
        try:
            result = await get_homefeed(client, category=category, num=count)
            for item in result.items:
                print(f"📝 {item.title}")
                print(f"   ID: {item.note_id} | 作者: {item.user.nickname if item.user else 'N/A'}")
            print(f"\n共 {len(result.items)} 条 (has_more={result.has_more})")
        finally:
            await client.close()

    asyncio.run(_run())
