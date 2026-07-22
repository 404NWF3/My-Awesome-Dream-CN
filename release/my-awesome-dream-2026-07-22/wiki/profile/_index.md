---
type: moc
title: "个人资产索引"
created: 2026-07-22
updated: 2026-07-22
tags:
  - moc
  - profile
status: seed
related:
  - "[[index]]"
sources: []
---

# 个人资产索引

薄业务索引层（路 C）：本页不装实体，用 [[dataview|Dataview]] 聚合 `wiki/entities/` 里用户本人画像相关页 + SWOT，并链接 [[profile]] 下衍生的资产子页（科研、竞赛等）。

## SWOT（来自用户本人画像页）

```dataview
TABLE WITHOUT ID
  file.link AS 画像, 优势, 劣势, 机会, 威胁
FROM "wiki/entities"
WHERE entity_type = "person" AND tags.contains("user-self")
```

## 资产子页（衍生）

```dataview
TABLE WITHOUT ID file.link AS 页, updated AS 最近更新
FROM "wiki/profile"
WHERE type != "moc"
SORT updated DESC
```

## 维护

- 用户本人画像：在 `wiki/entities/` 建 `type: entity`（`entity_type: person`，加 `tag: user-self`），SWOT 字段填入。
- 衍生子页（成绩/科研/竞赛/英语与技能）：放在 `wiki/profile/` 衍生页。