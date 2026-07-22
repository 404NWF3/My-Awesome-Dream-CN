# `.archive/` — 冷来源归档

`lint the wiki` 命令把符合冷判据的 `.raw/` 原始文件 + `.meta.yaml` 迁入此处，保持 `.raw/` 干净。

## 冷判据（必须同时满足）

1. `.raw/` 文件的 `status` 为 `superseded`（内容被新指纹替代）。
2. 最近 60 天无 wikilink 新增引用该来源。

## 移什么、留什么

- 移：`.raw/` 的原始文件 + `.meta.yaml`，按原结构迁入 `.archive/<同结构>/`。
- **不移**：`wiki/sources/` 的 md——它是 wiki 的一部分，wikilink 要能跳到。移的只是证据层，不是消化层。

## 归档后 wikilink 不产生死链

wikilink 指向 `wiki/sources/` 中 source md 的 slug，不指向 `.raw/` 文件。归档只搬原始文件，跳转目标不受影响。source md 正文前排会加一行 `> 原始已归档（fingerprint=…），见 .archive/`。

> release 版本中本目录为空。