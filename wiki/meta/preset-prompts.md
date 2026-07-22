---
type: meta
title: "预设提示词清单"
created: 2026-07-22
updated: 2026-07-22
tags: [meta, preset-prompts]
status: stub
---

# 预设提示词清单

预设提示词是 grill-me-study 深挖到对应分支时**可调用的弹药库**：调出对应提示词让用户作答，回复沉淀进 `wiki/questions/`（`prompt_type: preset`、`preset_slug` 对应本页条目），被展示面板第 4 区命中。

## 录入状态

具体提示词条目**留到跑过一次 grill-me-study 后逐条设计**（现在定会脱离实际——还没用过 grill-me-study 验证过一次）。

## 条目结构约定（待录入）

每条预设提示词按下面结构录入，`preset_slug` 用于和 `wiki/questions/` 沉淀文件里的 frontmatter `preset_slug` 对应：

```
- preset_slug: goal-clarify
  适用于: 决策树 Q1——读研动机挖掘
  原文: "我是一名大三学生，帮我一步步厘清保研方向……"

- preset_slug: target-match
  适用于: 决策树 Q6——目标院校层匹配
  原文: "结合我的画像，帮我判断哪些目标院校匹配度高……"
```

## 注

- preset_slug 一旦录入就**不再变更**（沉淀文件靠它回链），新增走新 slug。
- 提示词原文更新 = 新 slug（旧条目保留，老沉淀仍能命中）。