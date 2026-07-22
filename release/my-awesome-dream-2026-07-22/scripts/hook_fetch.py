"""hook_fetch.py — Claude Code Stop hook 调度器.

每次 Claude 会话结束触发一次。读 config.yaml 各来源 frequency + .last_run.yaml 时间戳,
按各来源频率决定是否跑该来源抓取。产物只写 .raw/（社区域铁律：禁写 wiki/）.

非真定时：抓取时机受限于"Claude 会话结束"而非绝对时间——用户接受此约束.
设计见 Project Develop Plan.md「Hook 机制」.

退出码：始终 exit 0（不阻断 Claude 停止）. 抓取失败只记日志, 不 block 会话.

真实调用能力边界（grilled 后核实）：
- wechat-article-search：可从 config.wechat.keywords 直接跑（Node search_wechat.js）.
- sufe-cli：可跑 `sufe score list`，但需用户先 `sufe auth`（首次）.
- zhihu-fetch / rednote-skill：读取 config 中收藏夹 URL / 用户 ID；缺入参时跳过并提示.
- 目标院校官网：由 scripts/fetch_official_page.py 使用 Playwright 库真实抓取.
- `--full`：忽略时间戳与频率，供首次或手动全量采集使用.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

VAULT = Path(__file__).resolve().parent.parent
CONFIG = VAULT / "config.yaml"
RAW = VAULT / ".raw"
LAST_RUN_FILE = VAULT / ".last_run.yaml"

SKILLS = VAULT / ".claude" / "skills"
WECHAT_JS = SKILLS / "wechat-article-search" / "scripts" / "search_wechat.js"
ZHIHU_COLLECTION = SKILLS / "zhihu-fetch" / "scripts" / "fetch_zhihu_collection.py"
ZHIHU_BATCH = SKILLS / "zhihu-fetch" / "scripts" / "fetch_zhihu_batch.py"
OFFICIAL_FETCH = VAULT / "scripts" / "fetch_official_page.py"
PYTHON = Path(sys.executable)

def now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def load_config() -> dict[str, Any]:
    if not CONFIG.exists():
        return {}
    with CONFIG.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_last_run() -> dict[str, Any]:
    if not LAST_RUN_FILE.exists():
        return {}
    with LAST_RUN_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_last_run(data: dict[str, Any]) -> None:
    with LAST_RUN_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=True)


def hours_since(ts: str | None) -> float:
    if not ts:
        return float("inf")
    try:
        return (datetime.datetime.now() - datetime.datetime.fromisoformat(ts)).total_seconds() / 3600
    except ValueError:
        return float("inf")


def fingerprint(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str]:
    """跑一条命令，返回 (返回码, stdout+stderr 合并). 失败不抛."""
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 99, f"[run-error] {e}"


def ensure_raw_dir(rel: str) -> Path:
    d = RAW / rel
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── 各来源抓取 ──

def fetch_official(cfg: dict, last_run: dict) -> list[str]:
    """目标院校官网（天级）. 真实调用 scripts/fetch_official_page.py（Playwright 库，非 MCP）."""
    pages = [p for p in cfg.get("watched_pages", []) if p.get("url")]
    if not pages:
        return []
    freq_h = pages[0].get("frequency_days", 1) * 24
    if hours_since(last_run.get("official")) < freq_h:
        return []
    msgs = []
    for p in pages:
        rc, log = run([
            str(PYTHON), str(OFFICIAL_FETCH),
            "--url", p["url"],
            "--school", str(p.get("school", "")),
            "--college", str(p.get("college", "")),
            "--slug", str(p.get("page_slug", "")),
        ], cwd=VAULT, timeout=180)
        tail = log.strip().splitlines()[-1][:120] if log.strip() else ""
        msgs.append(f"[official] {p.get('school')}/{p.get('college')}/{p.get('page_slug')} rc={rc} {tail}")
    return msgs


def fetch_wechat(cfg: dict, last_run: dict) -> list[str]:
    """公众号（wechat-article-search skill，Node）. 可直接跑：node search_wechat.js <kw> -o <path>.json."""
    w = cfg.get("wechat", {})
    if hours_since(last_run.get("wechat")) < w.get("frequency_hours", 1):
        return []
    kws = w.get("keywords") or []
    if not kws:
        return []
    if not WECHAT_JS.exists():
        return [f"[wechat] 脚本缺失：{WECHAT_JS}"]
    out_dir = ensure_raw_dir("community-info/wechat")
    msgs = []
    for kw in kws:
        # 每个 kw 一份 JSON，文件名用 kw slug（JSON 内含多篇文章，去重交由 convert 那跳按正文指纹处理）.
        slug = "".join(c if c.isalnum() else "_" for c in kw)[:32] or "query"
        out_json = out_dir / f"{slug}.json"
        rc, log = run(["node", str(WECHAT_JS), kw, "-n", "20", "-o", str(out_json)], timeout=180)
        ok = rc == 0 and out_json.exists()
        msgs.append(f"[wechat] kw={kw!r} rc={rc} out={out_json.name} {'✅' if ok else '❌'}")
    return msgs


def fetch_community(cfg: dict, last_run: dict) -> list[str]:
    """社区（zhihu / rednote）. 有入参时真实抓取，缺参跳过并提示.
    - zhihu: fetch_zhihu_collection.py（列表）→ fetch_zhihu_batch.py（正文，输出目录=.raw/community-info/zhihu/）
    - rednote: rednote report daily -u <uid> -o .raw/community-info/rednote/"""
    c = cfg.get("community", {})
    if hours_since(last_run.get("community")) < c.get("frequency_hours", 1):
        return []
    msgs = []

    # zhihu
    zurl = (c.get("zhihu_collection_url") or "").strip()
    if zurl and ZHIHU_COLLECTION.exists():
        list_rc, list_log = run([str(PYTHON), str(ZHIHU_COLLECTION), zurl, "50"], cwd=VAULT, timeout=300)
        if list_rc == 0:
            # collection json 输出到 OPENCLAW_WORKSPACE（默认 ~/.openclaw/workspace/）；
            # 找出刚生成的列表文件，再跑 batch 抓正文到 .raw/community-info/zhihu/
            import glob as _glob
            ws = Path(os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
            cands = sorted(ws.glob("zhihu_collection_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if cands:
                out_dir = ensure_raw_dir("community-info/zhihu")
                b_rc, b_log = run([str(PYTHON), str(ZHIHU_BATCH), str(cands[0]), str(out_dir)], cwd=VAULT, timeout=600)
                msgs.append(f"[zhihu] collection ✓ batch rc={b_rc} → .raw/community-info/zhihu/")
            else:
                msgs.append("[zhihu] collection 列表已抓但未找到输出 json")
        else:
            msgs.append(f"[zhihu] collection 抓取失败 rc={list_rc}: {list_log.strip().splitlines()[-1][:100] if list_log.strip() else ''}")
    elif not zurl:
        msgs.append("[zhihu·缺入参] config.community.zhihu_collection_url 为空；填入收藏夹 URL 后自动抓")

    # rednote
    uid = (c.get("rednote_user_id") or "").strip()
    if uid:
        out_dir = ensure_raw_dir("community-info/rednote")
        r_rc, r_log = run(["uv", "run", "rednote", "report", "daily", "-u", uid, "-o", str(out_dir)], cwd=VAULT, timeout=600)
        msgs.append(f"[rednote] daily rc={r_rc} → .raw/community-info/rednote/")
    else:
        msgs.append("[rednote·缺入参] config.community.rednote_user_id 为空；填入 UID 后自动抓")

    if not (c.get("knowledge_keywords") or c.get("target_keywords")) and not zurl and not uid:
        return []
    return msgs


def fetch_sufe(cfg: dict, last_run: dict) -> list[str]:
    """sufe-cli 周级（上财学生）. 跑 `sufe score list`，TSV 重定向落 .raw/myself/.
    需用户先 `sufe auth`. 用 uv run sufe 调用. 成绩归 source/myself，成绩单不作独立来源."""
    s = cfg.get("sufe", {})
    if not s.get("enabled"):
        return []
    if hours_since(last_run.get("sufe")) < s.get("frequency_weeks", 1) * 7 * 24:
        return []
    out_dir = ensure_raw_dir("myself")
    out_tsv = out_dir / "scores.tsv"
    # `uv run sufe score list` 输出 TSV 到 stdout，拖到这里.
    rc, log = run(["uv", "run", "sufe", "score", "list"], cwd=VAULT, timeout=180)
    if rc != 0:
        return [f"[sufe] 调用失败 rc={rc}（是否未 `sufe auth`？）: {log[:160]}"]
    out_tsv.write_text(log, encoding="utf-8")
    # 同目录写 .meta.yaml（成绩数据 source_type=score）.
    fp = fingerprint(log.encode("utf-8"))
    meta = {
        "fingerprint": fp, "source_type": "score", "source_layer": "myself",
        "fetched_at": now_iso(), "origin": {"channel": "sufe-cli", "url": "", "account_or_school": "本校", "page_slug": ""},
        "title": "成绩与绩点", "status": "pending", "related_source_note": "",
    }
    with (out_dir / "scores.tsv.meta.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)
    return [f"[sufe] ✅ 成绩 TSV → {out_tsv.name} (fp={fp})"]


FETCHERS = {
    "official": fetch_official,
    "wechat": fetch_wechat,
    "community": fetch_community,
    "sufe": fetch_sufe,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按 config.yaml 抓取保研信息源")
    parser.add_argument(
        "--full",
        action="store_true",
        help="忽略 .last_run.yaml 的频率限制，立即尝试所有已启用来源（首次全量采集使用）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = load_config()
    if not cfg:
        print("[hook_fetch] 无 config.yaml，跳过（用户未运行 /init？）")
        return 0
    last_run = {} if args.full else load_last_run()
    if args.full:
        print("[hook_fetch] 首次/手动全量模式：忽略频率，尝试所有已启用来源。")
    all_msgs: list[str] = []
    touched: dict[str, str] = {}
    for key, fn in FETCHERS.items():
        msgs = fn(cfg, last_run)
        if msgs:
            all_msgs.extend(msgs)
            touched[key] = now_iso()
    if touched:
        save_last_run({**last_run, **touched})
        print("[hook_fetch] 本轮触发:\n" + "\n".join(all_msgs))
    else:
        if args.full:
            print("[hook_fetch] 未发现已启用且入参完整的来源，跳过抓取。")
        else:
            print("[hook_fetch] 本轮无来源到频率，跳过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
