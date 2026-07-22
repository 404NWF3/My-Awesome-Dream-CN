"""convert_raw_to_sources.py — .raw → wiki/sources 转换管线（第一跳）.

读取 .raw/ 下 status=pending 的原始文件，转成 wiki/sources/ 下的 source md
(type: source, 正文=初步转 md 全文). 提炼发生在下游 ingest（source→concept/entity）,
本脚本只做最初步的格式转换 + frontmatter 对齐.

去重语义（grill 2026-07-22）:
- 指纹不变、只是 convert 逻辑升级想重跑 → source md 覆盖.
- 指纹变（内容真改）→ 新 .raw 文件 + 旧 status 标 superseded + 产新 source 页.

设计见 Project Develop Plan.md「ingest 去重」「wiki/sources frontmatter」.
"""
from __future__ import annotations

import datetime
import hashlib
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Any

VAULT = Path(__file__).resolve().parent.parent
RAW = VAULT / ".raw"
SOURCES = VAULT / "wiki" / "sources"


def now_date() -> str:
    return datetime.date.today().isoformat()


def fingerprint_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def to_markdown(raw: Path) -> str:
    """原始字节 → 初步 md. PDF/DOCX/HTML 各自转，纯文本直接读."""
    suffix = raw.suffix.lower()
    try:
        if suffix in (".md", ".markdown", ".txt"):
            return raw.read_text(encoding="utf-8")
        if suffix == ".html":
            # 粗转：用 pandoc 优先，否则剥标签的朴素 fallback.
            try:
                out = subprocess.run(["pandoc", "-f", "html", "-t", "markdown", str(raw)], capture_output=True, text=True, check=True).stdout
                return out
            except Exception:
                import re
                txt = re.sub(r"<[^>]+>", "", raw.read_text(encoding="utf-8", errors="ignore"))
                return txt.strip()
        if suffix in (".pdf", ".docx", ".doc"):
            try:
                out = subprocess.run(["pandoc", "-t", "markdown", str(raw)], capture_output=True, text=True, check=True).stdout
                return out
            except Exception as e:
                return f"> [convert] 暂未能解析 {suffix}（pandoc 缺失？{e}），请人工或后续 ingest 处理.\n\nContent: TODO"
        # 其它二进制：先占位，交由后续 ingest/agent 提炼.
        return f"> [convert] 未识别格式 {suffix}，留待 ingest agent 处理."
    except Exception as e:
        return f"> [convert] 转换失败：{e}"


def slugify(title: str) -> str:
    keep = "".join(c if c.isalnum() or c in "._-" else "-" for c in (title or "untitled"))
    return keep.strip("-") or "untitled"


def meta_for(raw: Path, fingerprint: str) -> dict[str, Any]:
    meta_path = raw.with_suffix(raw.suffix + ".meta.yaml")
    if meta_path.exists():
        with meta_path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    # 缺 meta 则最小推断.
    return {
        "fingerprint": fingerprint,
        "source_type": "resume" if "myself" in raw.parts else ("official" if "my-dream-school" in raw.parts else "community"),
        "source_layer": "myself" if "myself" in raw.parts else ("my-dream-school" if "my-dream-school" in raw.parts else "community-info"),
        "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "origin": {"channel": "local-upload", "url": "", "account_or_school": "", "page_slug": ""},
        "title": raw.stem,
        "status": "pending",
    }


def make_source_md(raw: Path, meta: dict[str, Any]) -> Path:
    fp = meta["fingerprint"]
    title = meta.get("title") or raw.stem
    slug = slugify(title)
    fm = {
        "type": "source",
        "title": title,
        "status": "processed",
        "created": now_date(),
        "updated": now_date(),
        "raw_fingerprint": fp,
        "source_type": meta.get("source_type", ""),
        "origin": meta.get("origin", {}),
        "evidence_tier": "official" if meta.get("source_type") in ("official", "resume", "score") else "community",
        "valid_until": meta.get("valid_until", ""),
        "account_or_school": (meta.get("origin") or {}).get("account_or_school", ""),
        "tags": ["source"],
    }
    body = to_markdown(raw)
    out = SOURCES / f"{slug}.md"
    content = "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip() + "\n---\n\n# " + title + "\n\n" + body + "\n"
    overwrite = out.exists()
    out.write_text(content, encoding="utf-8")
    # 翻转 .raw 的 status 为 processed.
    meta["status"] = "processed"
    meta["related_source_note"] = f"[[sources/{slug}]]"
    with raw.with_suffix(raw.suffix + ".meta.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)
    return out


def main() -> int:
    SOURCES.mkdir(parents=True, exist_ok=True)
    pending = []
    for p in RAW.rglob("*"):
        if not p.is_file():
            continue
        if p.name.endswith(".meta.yaml") or p.name in (".gitkeep", "README.md"):
            continue
        meta_path = p.with_suffix(p.suffix + ".meta.yaml")
        status = "pending"
        if meta_path.exists():
            status = (yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}).get("status", "pending")
        if status == "pending":
            pending.append(p)
    if not pending:
        print("[convert] .raw/ 无 pending 文件.")
        return 0
    produced = []
    for p in pending:
        fp = fingerprint_file(p)
        meta = meta_for(p, fp)
        meta["fingerprint"] = fp
        out = make_source_md(p, meta)
        produced.append(str(out))
    print(f"[convert] 产出 {len(produced)} 篇 source md:\n" + "\n".join(produced))
    return 0


if __name__ == "__main__":
    sys.exit(main())