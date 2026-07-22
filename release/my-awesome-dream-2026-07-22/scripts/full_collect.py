"""首次/手动全量采集编排器。

第一阶段强制抓取所有已启用来源并完成 `.raw -> wiki/sources`；Claude Code 随后
对本轮新增/更新的 source 执行 wiki-ingest，最后用 ``--finish`` 生成统一汇报。

用法：
    uv run python scripts/full_collect.py
    uv run python scripts/full_collect.py --finish
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

VAULT = Path(__file__).resolve().parent.parent
STATE = VAULT / ".full_collect_state.json"

RAW_GROUPS = {
    "目标院校官网": VAULT / ".raw" / "my-dream-school",
    "公众号": VAULT / ".raw" / "community-info" / "wechat",
    "知乎": VAULT / ".raw" / "community-info" / "zhihu",
    "小红书": VAULT / ".raw" / "community-info" / "rednote",
    "个人材料/成绩": VAULT / ".raw" / "myself",
}

WIKI_GROUPS = {
    "source": VAULT / "wiki" / "sources",
    "entity": VAULT / "wiki" / "entities",
    "concept": VAULT / "wiki" / "concepts",
    "profile": VAULT / "wiki" / "profile",
    "question": VAULT / "wiki" / "questions",
}

IGNORED_NAMES = {".gitkeep", "README.md", "_index.md"}


def load_config() -> dict[str, Any]:
    path = VAULT / "config.yaml"
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError):
        return {}


def skipped_sources(config: dict[str, Any]) -> list[str]:
    skipped: list[str] = []
    if not any(page.get("url") for page in config.get("watched_pages", [])):
        skipped.append("目标院校官网：未配置 `watched_pages[].url`")
    if not (config.get("wechat", {}).get("keywords") or []):
        skipped.append("公众号：未配置 `wechat.keywords`")
    community = config.get("community", {})
    if not (community.get("zhihu_collection_url") or "").strip():
        skipped.append("知乎：未配置 `community.zhihu_collection_url`")
    if not (community.get("rednote_user_id") or "").strip():
        skipped.append("小红书：未配置 `community.rednote_user_id`")
    if not config.get("sufe", {}).get("enabled"):
        skipped.append("上财成绩：`sufe.enabled` 未启用")
    return skipped


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def index_files(root: Path, *, raw: bool = False) -> dict[str, str]:
    if not root.exists():
        return {}
    indexed: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in IGNORED_NAMES:
            continue
        if raw and path.name.endswith(".meta.yaml"):
            continue
        if not raw and path.suffix.lower() != ".md":
            continue
        indexed[path.relative_to(VAULT).as_posix()] = file_hash(path)
    return indexed


def frontmatter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            return {}
        _, yaml_text, _ = text.split("---", 2)
        return yaml.safe_load(yaml_text) or {}
    except (OSError, UnicodeError, ValueError, yaml.YAMLError):
        return {}


def filtered_markdown(
    roots: list[Path], predicate: Callable[[dict[str, Any]], bool] | None = None
) -> dict[str, str]:
    result: dict[str, str] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.md")):
            if path.name in IGNORED_NAMES:
                continue
            if predicate is not None and not predicate(frontmatter(path)):
                continue
            result[path.relative_to(VAULT).as_posix()] = file_hash(path)
    return result


def dashboard_snapshot() -> dict[str, dict[str, str]]:
    return {
        "1 最新高时效信息": filtered_markdown(
            [WIKI_GROUPS["entity"], WIKI_GROUPS["concept"]],
            lambda fm: fm.get("时效标签") == "current" and fm.get("evidence_tier") == "official",
        ),
        "2 官方来源信息": filtered_markdown(
            [WIKI_GROUPS["source"]],
            lambda fm: fm.get("evidence_tier") == "official",
        ),
        "3 个人 SWOT": filtered_markdown([WIKI_GROUPS["profile"]]),
        "4 高分问答沉淀": filtered_markdown(
            [WIKI_GROUPS["question"]],
            lambda fm: fm.get("prompt_type") in {"preset", "freeform"}
            and isinstance(fm.get("score"), (int, float))
            and fm["score"] >= 4,
        ),
    }


def snapshot() -> dict[str, Any]:
    return {
        "raw": {name: index_files(path, raw=True) for name, path in RAW_GROUPS.items()},
        "wiki": {name: index_files(path) for name, path in WIKI_GROUPS.items()},
        "dashboard": dashboard_snapshot(),
    }


def delta(before: dict[str, str], after: dict[str, str]) -> dict[str, Any]:
    added = sorted(set(after) - set(before))
    updated = sorted(path for path in set(before) & set(after) if before[path] != after[path])
    return {"added": added, "updated": updated, "total": len(after)}


def run(command: list[str], timeout: int) -> tuple[int, str]:
    process = subprocess.run(
        command,
        cwd=VAULT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    output = ((process.stdout or "") + (process.stderr or "")).strip()
    return process.returncode, output


def changed_source_paths(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    change = delta(before["wiki"]["source"], after["wiki"]["source"])
    return change["added"] + change["updated"]


def start() -> int:
    config = load_config()
    before = snapshot()
    print("[full-collect] 1/3 强制抓取 config.yaml 中所有已启用来源……")
    fetch_rc, fetch_output = run(
        [sys.executable, str(VAULT / "scripts" / "hook_fetch.py"), "--full"],
        timeout=1800,
    )
    if fetch_output:
        print(fetch_output)

    print("[full-collect] 2/3 转换本轮 pending 原始材料到 wiki/sources……")
    convert_rc, convert_output = run(
        [sys.executable, str(VAULT / "scripts" / "convert_raw_to_sources.py")],
        timeout=1800,
    )
    if convert_output:
        print(convert_output)

    after = snapshot()
    state = {
        "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "before": before,
        "after_collect": after,
        "fetch_rc": fetch_rc,
        "fetch_output": fetch_output,
        "convert_rc": convert_rc,
        "convert_output": convert_output,
        "skipped_sources": skipped_sources(config),
    }
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    sources = changed_source_paths(before, after)
    print(f"[full-collect] 3/3 第一阶段完成：本轮新增/更新 {len(sources)} 篇 source。")
    for path in sources:
        print(f"  - {path}")
    if sources:
        print("[full-collect] Claude Code：请立即对以上 source 执行批量 wiki-ingest，再运行 --finish。")
    else:
        print("[full-collect] 没有新增/更新的 source；仍请运行 --finish 生成本轮汇报。")
    return 0 if fetch_rc == 0 and convert_rc == 0 else 1


def warning_lines(output: str) -> list[str]:
    markers = ("失败", "缺入参", "缺失", "❌", "run-error", "rc=1", "rc=2", "rc=99")
    return [line.strip() for line in output.splitlines() if any(marker in line for marker in markers)]


def finish() -> int:
    if not STATE.exists():
        print("[full-collect] 找不到本轮状态；请先运行 `uv run python scripts/full_collect.py`。")
        return 2

    state = json.loads(STATE.read_text(encoding="utf-8"))
    before = state["before"]
    after_collect = state["after_collect"]
    final = snapshot()

    print("\n# 全量信息采集与沉淀完成")
    print(f"\n开始时间：{state['started_at']}")
    print("\n## 采集了什么")
    print("\n| 来源 | 新增原始文件 | 更新原始文件 | 当前总数 |")
    print("|---|---:|---:|---:|")
    for name in RAW_GROUPS:
        change = delta(before["raw"][name], after_collect["raw"][name])
        print(f"| {name} | {len(change['added'])} | {len(change['updated'])} | {change['total']} |")

    print("\n## 沉淀了什么")
    print("\n| 页面类型 | 新增 | 更新 | 当前总数 |")
    print("|---|---:|---:|---:|")
    for name in WIKI_GROUPS:
        change = delta(before["wiki"][name], final["wiki"][name])
        print(f"| {name} | {len(change['added'])} | {len(change['updated'])} | {change['total']} |")

    print("\n## dashboard 哪些区有变化")
    print("\n| 区域 | 新增条目 | 更新条目 | 当前条目 |")
    print("|---|---:|---:|---:|")
    changed_sections = 0
    for name, after_index in final["dashboard"].items():
        change = delta(before["dashboard"][name], after_index)
        if change["added"] or change["updated"]:
            changed_sections += 1
        print(f"| {name} | {len(change['added'])} | {len(change['updated'])} | {change['total']} |")
    if not changed_sections:
        print("\n本轮没有新增命中 dashboard 过滤条件的条目。若已采集社区材料，它仍保存在 `wiki/sources/`，可继续提问或补充画像/评分。")

    warnings = warning_lines(state.get("fetch_output", ""))
    if warnings:
        print("\n## 需要补救的来源")
        for warning in warnings:
            print(f"- {warning}")

    skipped = state.get("skipped_sources", [])
    if skipped:
        print("\n## 未启用或因缺配置跳过的来源")
        for item in skipped:
            print(f"- {item}")

    print("\n## 最终结果在哪里看")
    print("\n**现在请在 Obsidian 中打开 `wiki/meta/dashboard.md`。**")
    print("以后每次完成采集、ingest 或 grill 后，都优先回到这个“保研驾驶舱”查看最新结果。")

    STATE.unlink(missing_ok=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="首次/手动全量信息采集与汇报")
    parser.add_argument("--finish", action="store_true", help="wiki-ingest 完成后输出统一汇报")
    args = parser.parse_args(argv)
    return finish() if args.finish else start()


if __name__ == "__main__":
    raise SystemExit(main())
