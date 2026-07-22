---
type: moc
title: "目标院校索引"
created: 2026-07-22
updated: 2026-07-22
tags:
  - moc
  - targets
status: seed
related:
  - "[[index]]"
  - "[[requirements/_index|保研规则索引]]"
sources: []
---

# 目标院校索引

薄业务索引层（路 C）：本页不装实体，只用 [[dataview|Dataview]] 聚合 `wiki/entities/` 里 `entity_type=org` 的目标院校实体页。每个院校/学院/项目一页（放在 entities/，不在本目录）。

```dataview
TABLE WITHOUT ID
  file.link AS 院校, entity_type AS 类型, 时效标签, valid_until AS 截止, evidence_tier AS 分层
FROM "wiki/entities"
WHERE entity_type = "org"
SORT 时效标签 ASC, valid_until ASC
```

## 维护

- 新增目标院校：在 `wiki/entities/` 建 `type: entity` 页（`entity_type: org`），本页自动聚合。
- 不要在本目录建实体页，实体页只在 `wiki/entities/`。
- 详见 [[comparisons|对比分析]] 做院校间对比。