---
type: moc
title: "问答索引"
created: 2026-07-22
updated: 2026-07-22
tags:
  - moc
  - questions
status: seed
related:
  - "[[index]]"
sources: []
---

# 问答索引

Claudian 与 grill-me-study 的回复沉淀于此（type: question）。frontmatter 带 `prompt_type`/`preset_slug`/`score`/`asked_at`/`answered_by`。

## 高分问答（score ≥ 4）

```dataview
TABLE WITHOUT ID
  question AS 提问, score AS 评分, prompt_type AS 类型, answered_by AS 来源, file.link AS 回答
FROM "wiki/questions"
WHERE type = "question" AND score >= 4
SORT asked_at DESC
```

## 全部问答（按时间）

```dataview
TABLE WITHOUT ID
  question AS 提问, score AS 评分, asked_at AS 时间, file.link AS 回答
FROM "wiki/questions"
WHERE type = "question"
SORT asked_at DESC
```

> release 版本中本目录为空骨架，用户的问答沉淀不入 release（克隆目录填）。