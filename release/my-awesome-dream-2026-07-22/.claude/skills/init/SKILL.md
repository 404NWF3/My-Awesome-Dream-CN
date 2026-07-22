---
name: init
description: 保研 Harness 初始化技能。用户 clone release 后首次运行，引导完成环境依赖、配置、骨架生成、首份简历投放与 grill-me-study 引导。
---

# 初始化技能

引导新用户在 clone release 后完成初始化。按顺序执行，每步等用户确认再继续。

## 1 环境依赖检查

- 检查 Python 与 uv（按 OS 给安装命令）
- 检查 Node.js 与 `cheerio`（wechat-article-search 依赖）
- 询问是否上财学生：
  - 是 → 提示安装 sufe-cli（`uv tool install sufe-cli && sufe install`），设 `config.yaml` 的 `user.is_sufe=true`
  - 否 → 跳过 sufe，本技能不自动装
- 询问目标院校是否有官网需监视（为下一步配置铺垫）

## 2 填写 config.yaml

**问清所有需要监视的网站**——逐项问，写入项目根 `config.yaml`：

- 用户本人：姓名、本科院校
- 目标院校官网列表（可多个院校，每个院校多个学院页面）：school / college / url / page_slug / frequency_days
- 公众号 accounts + keywords
- 社区 knowledge_keywords + target_keywords
- is_sufe / sufe.enabled

## 3 生成骨架

- 确保 `.raw/` 空骨架（含 README 说明"在此放你的来源"）
- 确保 `wiki/` 空骨架已含种子保研术语概念页（夏令营/预推免/九推等）
- 确保 `wiki/meta/preset-prompts.md` 占位

## 4 投放第一份简历

- 提示用户把简历（PDF/DOCX）放入 `.raw/myself/resume/`
- 触发首次 ingest（`.raw` → `wiki/sources` → wiki 本体），建立用户本人 entity

## 5 引导 grill-me-study

- 提示运行 `/grill-me-study` 开始保研方向 grill
- 告知产物将沉淀进 `wiki/questions/` 并出现在 dashboard 第 4 区