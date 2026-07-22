# `wiki/sources/` — 来源摘要层

每个 `.raw/` 原始文件经 `scripts/convert_raw_to_sources.py` 转换出**一页 source md**（`type: source`），放在这里。正文 = 初步转 md 全文（最接近原始，不做提炼）；提炼在下游 `wiki/concepts` / `wiki/entities`。

## 字段

frontmatter 含 `raw_fingerprint`（回指 `.raw/` 原始文件指纹）、`evidence_tier`、`valid_until`、`account_or_school`、`origin`。完整字段见 `_templates/source.md`。

## 去重

- 指纹相同、convert 逻辑升级重跑 → source md 覆盖。
- 指纹不同（内容真改） → 新 `.raw/` 文件 + 旧 status 标 `superseded` + 产新 source 页（与旧 source 并存，靠 `raw_fingerprint` 区分）。

> release 版本中本目录为空骨架，用户的来源摘要由 ingest 后产出。