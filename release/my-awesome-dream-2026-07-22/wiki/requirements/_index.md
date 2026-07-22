---
type: moc
title: "保研规则索引"
created: 2026-07-22
updated: 2026-07-22
tags:
  - moc
  - requirements
status: seed
related:
  - "[[index]]"
  - "[[targets/_index|目标院校索引]]"
sources: []
---

# 保研规则索引

薄业务索引层（路 C）：本页不装概念，用 [[dataview|Dataview]] 聚合 `wiki/concepts/` 里 `tag:保研规则` 的概念页（推免规则本质是机制，归类为 concept）。

## 本校推免资格规则（拿资格）

```dataview
TABLE WITHOUT ID file.link AS 规则, updated AS 最近更新, 时效标签
FROM "wiki/concepts"
WHERE contains(tags, "保研规则") AND account_or_school = "本校"
SORT updated DESC
```

## 目标院校接收规则（拿 offer）

```dataview
TABLE WITHOUT ID file.link AS 规则, account_or_school AS 院校, updated AS 最近更新
FROM "wiki/concepts"
WHERE contains(tags, "保研规则") AND account_or_school != "本校"
SORT updated DESC
```

## 维护

- 保研规则页：在 `wiki/concepts/` 建 `type: concept` + `tag: 保研规则`，本页自动聚合。
- 本校推免细则未入库 → 第一优先级材料，放入 `.raw/` 后 ingest。

> [!gap] 待补
> 本校推免细则文件尚未入库。这是决定能否拿到资格的**第一优先级**材料。