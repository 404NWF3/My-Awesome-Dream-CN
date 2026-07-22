---
type: dashboard
title: "保研驾驶舱"
created: 2026-07-22
updated: 2026-07-22
tags: [dashboard]
status: developing
---

# 保研驾驶舱

> 单个 markdown 面板 + 多段 dataview。Claudian 插件不嵌入。字段名须与各 frontmatter 一字不差对齐（见 CLAUDE.md）。

## 1 最新高时效信息（当季·官方）

```dataview
TABLE valid_until AS 截止日, account_or_school AS 院校, file.link AS 条目
FROM "wiki/entities" OR "wiki/concepts"
WHERE 时效标签 = "current" AND evidence_tier = "official"
SORT valid_until ASC
```

## 2 官方来源信息（含历史时间线）

```dataview
TABLE evidence_tier AS 分层, account_or_school AS 院校, valid_until AS 截止, file.link AS 条目
FROM "wiki/sources"
WHERE evidence_tier = "official"
SORT valid_until DESC
```

## 3 个人 SWOT

```dataview
TABLE WITHOUT ID
  file.link AS 画像,
  优势, 劣势, 机会, 威胁
FROM "wiki/profile"
```

## 4 高分问答沉淀

### 4A 预设提示词命中

```dataview
TABLE WITHOUT ID
  question AS 提示词, score AS 评分, asked_at AS 时间, file.link AS 回答
FROM "wiki/questions"
WHERE prompt_type = "preset" AND score >= 4
SORT asked_at DESC
```

### 4B 自由提问高分

```dataview
TABLE WITHOUT ID
  question AS 提问, score AS 评分, asked_at AS 时间, file.link AS 回答
FROM "wiki/questions"
WHERE prompt_type = "freeform" AND score >= 4
SORT asked_at DESC
```