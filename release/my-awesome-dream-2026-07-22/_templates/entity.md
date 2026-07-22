---
type: entity
title: "<% tp.file.title %>"
entity_type: person              # person | org | school | program
role: ""
first_mentioned: "[[]]"
created: <% tp.date.now("YYYY-MM-DD") %>
updated: <% tp.date.now("YYYY-MM-DD") %>
tags:
  - entity
status: seed
related: []
sources: []
# —— 用户本人画像（profile 衍生页）才填，其它实体留空 ——
优势: []
劣势: []
机会: []
威胁: []
# —— 字段对齐（grill 2026-07-22），供 dashboard dataview 聚合 ——
evidence_tier: official           # 官方来源的实体才 official；社区提及的 community
valid_until:                      # 可选，有截止事件（如招生）时填 YYYY-MM-DD
account_or_school: ""             # 所属院校/机构（org/user 自己留空）
时效标签: current                 # current | historical | stale-suspect（lint 自补段打）
evidence:                         # 多来源追踪，每个 entry 一条
  - source: "[[sources/某来源]]"
    evidence_tier: official|community
    confidence: high|medium|low
    captured_at: <% tp.date.now("YYYY-MM-DD") %>
disputed: false                   # 页内不同来源说法冲突
as_of: <% tp.date.now("YYYY-MM-DD") %>   # 信息基准日
---

# <% tp.file.title %>

## Overview

[Who or what this is. One paragraph.]

## Key Facts

-

## Connections

-

## Sources

-
