"""Report CLI commands."""

from __future__ import annotations

import asyncio
import typer
from rednote_core.crypto import generate_cookies
from rednote_core.client import XHSClient
from rednote_core.auth import load_cookies
from rednote_core.config import load_config
from rednote_core.apis import search_notes, get_user_notes
from rednote_core.report import render_search_report, render_daily_report

report_app = typer.Typer(help="报告生成", no_args_is_help=True)


def _get_client() -> XHSClient:
    config = load_config()
    saved = load_cookies(config["auth"]["cookies_file"])
    cookies = {
        **generate_cookies(),
        **saved,
        "loadts": str(int(__import__("time").time())),
        "webBuild": "6.12.3",
        "xsecappid": "xhs-pc-web",
    }
    return XHSClient(
        proxy=config["client"]["proxy"],
        cookies=cookies,
        timeout=config["client"]["timeout"],
        retry_interval=config["client"]["retry_interval"],
        request_interval=config["client"]["request_interval"],
    )


@report_app.command("daily")
def daily(
    user_id: str = typer.Option(..., "-u", "--user-id", help="用户 ID"),
    keyword: str = typer.Option("", "-k", "--keyword", help="同时搜索关键词"),
):
    """生成运营日报."""

    async def _run():
        client = _get_client()
        try:
            print(f"📊 采集用户 {user_id} 的笔记...")
            user_result = await get_user_notes(client, user_id, num=50)
            all_notes = user_result.notes

            if keyword:
                print(f"🔍 搜索关键词: {keyword}...")
                search_result = await search_notes(client, keyword=keyword, page_size=20)
                all_notes.extend(search_result.items)

            if not all_notes:
                print("⚠️  未采集到任何笔记")
                return

            path = render_daily_report(user_id, all_notes)
            print(f"✅ 日报已生成: {path}")
            print(f"   笔记数: {len(all_notes)}")
        finally:
            await client.close()

    asyncio.run(_run())
