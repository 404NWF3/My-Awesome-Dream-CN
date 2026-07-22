"""Login command — QR code authentication (RedCrack-compatible)."""

from __future__ import annotations

import asyncio
import time
import typer
from rednote_core.crypto import generate_cookies
from rednote_core.client import XHSClient
from rednote_core.auth import login_qrcode, check_login, save_cookies, load_cookies
from rednote_core.config import load_config

login_app = typer.Typer(help="认证管理")


@login_app.callback(invoke_without_command=True)
def login_default(ctx: typer.Context):
    """扫码登录小红书账号."""
    if ctx.invoked_subcommand is None:
        asyncio.run(_do_login())


async def _do_login():
    """Execute the QR login flow with RedCrack-compatible session init."""
    config = load_config()
    proxy = config["client"]["proxy"]

    # Create fully initialized session (scripting + gid + activate)
    print("📦 初始化会话...")
    client = await XHSClient.create(
        proxy=proxy,
        timeout=config["client"]["timeout"],
        retry_interval=config["client"]["retry_interval"],
        request_interval=0,
    )
    print(f"✅ 会话就绪: a1={client.cookies['a1'][:16]}...")

    try:
        print("📱 生成登录二维码...\n")
        new_cookies = await login_qrcode(client)

        all_cookies = {**client.cookies, **new_cookies}
        cookies_file = config["auth"]["cookies_file"]
        save_cookies(all_cookies, cookies_file)
        print(f"✅ Cookie 已保存到 {cookies_file}")

        client.update_cookies(new_cookies)
        if await check_login(client):
            print("✅ 登录验证成功！")
        else:
            print("⚠️  Cookie 已保存但验证失败，请重试")

    finally:
        await client.close()


@login_app.command("status")
def login_status():
    """检查当前登录状态."""
    config = load_config()
    cookies = load_cookies(config["auth"]["cookies_file"])

    if not cookies.get("web_session"):
        print("❌ 未登录 — 请运行 `rednote login`")
        return

    proxy = config["client"]["proxy"]

    async def _check():
        client = await XHSClient.create(proxy=proxy, web_session=cookies.get("web_session"))
        try:
            ok = await check_login(client)
            if ok:
                print("✅ 登录状态有效")
            else:
                print("❌ 登录已过期 — 请运行 `rednote login`")
        finally:
            await client.close()

    asyncio.run(_check())
