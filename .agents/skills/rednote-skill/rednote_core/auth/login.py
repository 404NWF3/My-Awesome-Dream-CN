"""QR code login flow for Xiaohongshu."""

from __future__ import annotations

import asyncio
import logging
import qrcode

logger = logging.getLogger(__name__)

EDITH_BASE = "https://edith.xiaohongshu.com"


async def login_qrcode(
    client,
    on_qr=None,
    poll_interval: float = 2.0,
    timeout: float = 120.0,
) -> dict:
    """Perform QR code login flow.

    1. Create QR code (POST /api/sns/web/v1/login/qrcode/create)
    2. Display QR code to user (via on_qr callback or terminal)
    3. Poll status (GET /api/sns/web/v1/login/qrcode/status)
    4. On success, extract cookies from response
    """
    # Step 1: Create QR code
    create_resp = await client.post(
        f"{EDITH_BASE}/api/sns/web/v1/login/qrcode/create",
        json_data={"qr_type": 1},
    )

    if create_resp.status_code != 200:
        raise RuntimeError(
            f"Failed to create QR code: {create_resp.status_code} {create_resp.text[:200]}"
        )

    qr_data = create_resp.json()
    if not qr_data.get("success"):
        raise RuntimeError(f"QR create failed: {qr_data.get('msg', 'unknown')}")

    qr_id = qr_data["data"]["qr_id"]
    code = qr_data["data"]["code"]
    qr_url = qr_data["data"].get("url", f"https://www.xiaohongshu.com/login?qr_code={code}")

    # Step 2: Display QR code
    if on_qr:
        on_qr({"qr_id": qr_id, "code": code, "url": qr_url})
    else:
        _print_qr_terminal(qr_url)

    # Step 3: Poll for scan
    elapsed = 0.0
    while elapsed < timeout:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

        status_resp = await client.get(
            f"{EDITH_BASE}/api/sns/web/v1/login/qrcode/status",
            params={"qr_id": qr_id, "code": code},
        )

        if status_resp.status_code != 200:
            continue

        status_data = status_resp.json()
        if not status_data.get("success"):
            continue

        code_status = str(status_data.get("data", {}).get("code_status", ""))

        if code_status == "2":
            # Scan successful! Extract cookies
            new_cookies = {}

            # Try response cookies
            for name, value in status_resp._cookies.items():
                if name in ("web_session", "sec_poison_id", "acw_tc"):
                    new_cookies[name] = value

            # Fallback: extract from set-cookie headers
            set_cookie = status_resp.headers.get("set-cookie", "")
            if "web_session=" in set_cookie and "web_session" not in new_cookies:
                for part in set_cookie.split(";"):
                    part = part.strip()
                    if part.startswith("web_session="):
                        new_cookies["web_session"] = part.split("=", 1)[1]

            # Last resort: scan all set-cookie headers
            if not new_cookies.get("web_session"):
                for header_name, header_value in status_resp.headers.items():
                    if header_name.lower() == "set-cookie":
                        for cookie_str in header_value.split(","):
                            cookie_str = cookie_str.strip()
                            for part in cookie_str.split(";"):
                                part = part.strip()
                                if "=" in part:
                                    key, val = part.split("=", 1)
                                    key = key.strip()
                                    if not key.startswith("_"):
                                        new_cookies[key] = val

            logger.info("Login successful!")
            return new_cookies

        elif code_status == "1":
            logger.debug("Waiting for scan...")
        elif code_status == "3":
            raise RuntimeError("QR code expired — please try again")
        elif code_status == "4":
            raise RuntimeError("Login was cancelled")

    raise TimeoutError(f"QR code scan timed out after {timeout}s")


def _print_qr_terminal(url: str) -> None:
    """Print QR code to terminal AND save as PNG for display."""
    import tempfile, os

    qr = qrcode.QRCode(border=2, box_size=10)
    qr.add_data(url)
    qr.make(fit=True)

    # Save PNG image
    img = qr.make_image(fill_color="black", back_color="white")
    png_path = os.path.join(tempfile.gettempdir(), "rednote_qrcode.png")
    img.save(png_path)

    # Also print ASCII art for terminal users
    ascii_qr = qrcode.QRCode(border=1)
    ascii_qr.add_data(url)
    ascii_qr.make(fit=True)
    ascii_qr.print_ascii(invert=True)

    print(f"\n📱 二维码图片已保存到: {png_path}")
    print(f"🔗 登录链接: {url}")
    print("请打开上方链接或用小红书APP扫描二维码")
    print("等待扫码... (超时: 120s)\n")


async def check_login(client) -> bool:
    """Check if current login session is valid."""
    try:
        resp = await client.get(
            "https://edith.xiaohongshu.com/api/sns/web/v2/user/me"
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("success", False)
        return False
    except Exception:
        return False
