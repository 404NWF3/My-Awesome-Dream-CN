---
type: moc
title: "概念索引"
created: 2026-07-22
updated: 2026-07-22
tags:
  - moc
  - concepts
status: seed
related:
  - "[[index]]"
sources: []
---

# 概念索引

薄业务索引层：用 [[dataview|Dataview]] 聚合 `wiki/concepts/`。保研机制概念（tag: 保研机制）与保研规则概念（tag: 保研规则）都在本目录。

## 所有概念

```dataview
TABLE WITHOUT ID file.link AS 概念, account_or_school AS 归属, 时效标签, updated AS 最近更新
FROM "wiki/concepts"
WHERE type = "concept"
SORT 时效标签 ASC, updated DESC
```

## 保研机制

```dataview
LIST
FROM "wiki/concepts"
WHERE contains(tags, "保研机制")
SORT file.name ASC
```

## 保研规则（聚合到 [[requirements/_index|保研规则索引]]）

```dataview
LIST
FROM "wiki/concepts"
WHERE contains(tags, "保研规则")
SORT file.name ASC
```

## 种子页（release 内置）

- [[夏令营]] / [[预推免]] / [[九推]] —— 三条拿 offer 通道
- [[推免资格]] / [[本校推免规则]] —— 资格前提