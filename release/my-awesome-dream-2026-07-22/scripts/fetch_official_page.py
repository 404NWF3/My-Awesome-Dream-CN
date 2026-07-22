"""fetch_official_page.py — 目标院校官网抓取（Playwright 库，不走 MCP）.

用法（由 hook_fetch.py 或手动调用）：
    .venv/Scripts/python scripts/fetch_official_page.py --url <url> --school <s> --college <c> --slug <page_slug>

产物：
    .raw/my-dream-school/<school>/<college>/<page_slug>/<fingerprint>.html
    .raw/my-dream-school/<school>/<college>/<page_slug>/<fingerprint>.html.meta.yaml

指纹去重：同一内容已存在则跳过（Plan D）。
反爬失败：返回非零并打印原因，由调用方决定是否沉淀专属反爬 skill（Plan 反爬策略）。
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import sys
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent


def fingerprint(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def fetch_html(url: str, timeout_ms: int = 30_000) -> str:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            return page.content()
        finally:
            browser.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--school", required=True)
    ap.add_argument("--college", required=True)
    ap.add_argument("--slug", required=True)
    args = ap.parse_args()

    out_dir = VAULT / ".raw" / "my-dream-school" / args.school / args.college / args.slug
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        html = fetch_html(args.url)
    except Exception as e:
        msg = str(e)
        print(f"[official] 抓取失败: {msg[:300]}", file=sys.stderr)
        if "Executable doesn't exist" in msg or "playwright install" in msg:
            print("[official] 提示：先运行 `uv run playwright install chromium` 安装浏览器", file=sys.stderr)
        return 1

    content = html.encode("utf-8")
    fp = fingerprint(content)
    dest = out_dir / f"{fp}.html"
    if dest.exists():
        print(f"[official] 内容未变化（fp={fp}），跳过落盘")
        return 0
    dest.write_bytes(content)

    meta = {
        "fingerprint": fp,
        "source_type": "official",
        "source_layer": "my-dream-school",
        "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "origin": {
            "channel": "official-site",
            "url": args.url,
            "account_or_school": args.school,
            "page_slug": args.slug,
        },
        "title": f"{args.school}{args.college}{args.slug}",
        "status": "pending",
        "related_source_note": "",
    }
    with (out_dir / f"{fp}.html.meta.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)

    print(f"[official] ✅ {args.school}/{args.college}/{args.slug} → {dest.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())