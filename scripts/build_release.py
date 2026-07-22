"""build_release.py — 打包 release（三轨隔离：工具轨 + 空骨架 + 公共资产，不含个人数据）.

输出：release/my-awesome-dream-<date>/  目录（可加 --zip 打成 zip）.

包含：
  - 工具轨：.claude/skills（剔除 _dev/）、_templates/、CLAUDE.md、README.md、config.yaml、
            scripts/、Project Develop Plan.md、.obsidian/ 配置（剔除 workspace.json / workspace-mobile.json）
  - 空骨架：.raw/（README + .gitkeep）、.archive/（README + .gitkeep）、
            wiki/ 目录结构 + 种子概念页 + meta 公共资产 + 各 README/MOC
  - 公共资产：wiki/meta/preset-prompts.md、wiki/meta/dashboard.md、wiki/entities/README.md 等

排除：
  - 个人数据轨：.raw/myself|my-dream-school|community-info 下任何实际内容、
    wiki/questions/ 用户沉淀、wiki/profile/ 个人画像页、wiki/sources/ 用户来源
  - 开发工具：.claude/skills/_dev/
  - 运行产物：.last_run.yaml、.venv/、__pycache__/、.git/、.smart-connections/

用法：
    python scripts/build_release.py            # 输出到 release/
    python scripts/build_release.py --zip      # 另打 zip
    python scripts/build_release.py --dry-run  # 只打印将包含/排除的文件
"""
from __future__ import annotations

import argparse
import datetime
import shutil
import sys
import zipfile
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
RELEASE_ROOT = VAULT / "release"

# ── 包含规则 ──

# 顶层文件：整文件包含
TOP_FILES = [
    "CLAUDE.md",
    "README.md",
    "Project Develop Plan.md",
    "config.yaml",
    ".gitignore",
]

# 目录：整个包含（内部再按排除规则过滤）
TOP_DIRS = [
    "_templates",
    "scripts",
]

# wiki/ 骨架：包含结构 + 公共资产，剔除用户数据
WIKI_INCLUDE = [
    "index.md", "log.md", "hot.md", "overview.md",
    "concepts",          # 含种子概念页（公共资产）
    "targets", "profile", "requirements",  # MOC 索引（只含 _index.md）
    "comparisons", "strategy",             # 空目录骨架
    "meta",              # dashboard.md + preset-prompts.md（公共资产）
    "entities",          # 只含 README.md + .gitkeep
    "sources",           # 只含 README.md + .gitkeep
    "questions",         # 只含 _index.md + .gitkeep（剔除用户沉淀）
]

# .obsidian/ 包含配置但剔除 workspace
OBSIDIAN_INCLUDE = ["app.json", "appearance.json", "community-plugins.json", "core-plugins.json", "graph.json", "types.json", "snippets", "plugins"]

# 排除：任何路径片段命中即排除
EXCLUDE_PARTS = {
    ".git", "__pycache__", ".venv", "node_modules", ".smart-connections",
    "_dev", ".trash",
}
EXCLUDE_FILES = {
    "workspace.json", "workspace-mobile.json", ".last_run.yaml",
    ".obsidian-git-data", ".DS_Store",
}


def is_excluded(rel: Path) -> bool:
    parts = set(rel.parts)
    if parts & EXCLUDE_PARTS:
        return True
    if rel.name in EXCLUDE_FILES:
        return True
    return False


def iter_tree(src: Path):
    for p in sorted(src.rglob("*")):
        if p.is_file():
            yield p


def collect() -> list[Path]:
    files: list[Path] = []

    # 顶层文件
    for name in TOP_FILES:
        p = VAULT / name
        if p.exists():
            files.append(p)

    # 顶层目录
    for name in TOP_DIRS:
        d = VAULT / name
        if d.exists():
            files.extend(p for p in iter_tree(d) if not is_excluded(p.relative_to(VAULT)))

    # .claude/skills（剔除 _dev）
    skills = VAULT / ".claude" / "skills"
    if skills.exists():
        files.extend(p for p in iter_tree(skills) if not is_excluded(p.relative_to(VAULT)))
    # .claude/settings.json
    settings = VAULT / ".claude" / "settings.json"
    if settings.exists():
        files.append(settings)

    # .obsidian 配置
    obs = VAULT / ".obsidian"
    if obs.exists():
        for item in OBSIDIAN_INCLUDE:
            p = obs / item
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(x for x in iter_tree(p) if not is_excluded(x.relative_to(VAULT)))

    # .raw / .archive 空骨架（只 README + .gitkeep，剔除任何实际内容）
    for rawdir in (VAULT / ".raw", VAULT / ".archive"):
        if rawdir.exists():
            for p in iter_tree(rawdir):
                rel = p.relative_to(VAULT)
                if p.name in ("README.md", ".gitkeep") and not is_excluded(rel):
                    files.append(p)

    # wiki/ 骨架
    wiki = VAULT / "wiki"
    if wiki.exists():
        for item in WIKI_INCLUDE:
            p = wiki / item
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(x for x in iter_tree(p) if not is_excluded(x.relative_to(VAULT)))

    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", action="store_true", help="另打 zip")
    ap.add_argument("--dry-run", action="store_true", help="只打印将包含的文件")
    args = ap.parse_args()

    files = collect()
    if args.dry_run:
        print(f"[release] 将包含 {len(files)} 个文件：")
        for p in files:
            print("  ", p.relative_to(VAULT))
        return 0

    stamp = datetime.date.today().isoformat()
    out_dir = RELEASE_ROOT / f"my-awesome-dream-{stamp}"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    for p in files:
        rel = p.relative_to(VAULT)
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)

    print(f"[release] ✅ 打包 {len(files)} 个文件 → {out_dir}")

    if args.zip:
        zip_path = RELEASE_ROOT / f"my-awesome-dream-{stamp}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in files:
                zf.write(p, p.relative_to(VAULT))
        print(f"[release] ✅ zip → {zip_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())