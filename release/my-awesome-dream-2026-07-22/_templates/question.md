---
type: question
title: "<% tp.file.title %>"
question: ""
answer_quality: draft
created: <% tp.date.now("YYYY-MM-DD") %>
updated: <% tp.date.now("YYYY-MM-DD") %>
tags:
  - question
status: developing
related: []
sources: []
# —— Claudian/Grill 回复沉淀字段（grill 2026-07-22）——
prompt_type: freeform             # preset | freeform（预设提示词命中 vs 自由提问）
preset_slug: ""                   # preset 命中填对应 slug；freeform 留空
score: 3                          # 1-5 用户打分；dashboard 第 4 区只展示 score>=4
asked_at: <% tp.date.now("YYYY-MM-DD") %>
answered_by: claudian              # claudian | grill-me
---

# <% tp.file.title %>

**Question:** [restate the original query]

## Answer

[The synthesized answer, with citations to specific wiki pages]

(Source: [[]])

## Confidence

[draft | solid | definitive] — [why]

## Related Questions

-
