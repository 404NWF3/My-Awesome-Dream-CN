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

### 1.5 社区来源登录（阻断性提醒）

在继续填写 config 之前，**逐项提醒用户完成以下登录**——未登录则对应来源的自动抓取无法生效：

- **小红书**：运行 `uv run rednote auth` 登录小红书账号（rednote-skill 依赖 Cookie 才能抓数据和生成报告）。
- **知乎**：zhihu-fetch 需浏览器 Cookie 持久化。提示用户在自己的浏览器登录知乎后运行 `uv run python .Codex/skills/zhihu-fetch/scripts/save_cookies.py`（或按该 skill 的 SKILL.md 最新指示操作）。
- **sufe（仅上财学生）**：`sufe auth` 登录上财门户（sufe-cli 依赖它才能拉成绩/绩点）。
- **公众号（wechat-article-search）**：无需登录，搜索即可。

> 逐一确认用户已完成对应项再进入下一步。

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

## 4.5 首次全量信息采集

配置和首份简历 ingest 完成后，**不要结束 `/init`，也不要只留一句让用户稍后自己运行的提示**。直接告诉用户：

> 配置已经完成，我现在开始首次全量信息采集。完成后会告诉你采集了什么、沉淀了什么，以及去哪里查看。

随后立即执行 `full-collect` 技能的完整流程。只有用户明确说“暂不采集”时才跳过，并把以下两个手动入口同时告诉用户：

```
/full-collect
根据我的 config.yaml，帮我做一次全量信息采集
```

`full-collect` 会按 config 配置**逐一跑所有已启用的来源**：

| 来源 | 做什么 | 产物去哪 |
|------|--------|---------|
| 目标院校官网 | Playwright 打开所有 `watched_pages` URL，取 HTML 全文 | `.raw/my-dream-school/<school>/<college>/<slug>/` |
| 公众号 | 搜索 `wechat.keywords` 中每个关键词，取文章列表 JSON | `.raw/community-info/wechat/` |
| 知乎 | 抓 `community.zhihu_collection_url` 收藏夹中所有文章的正文 + 图片 | `.raw/community-info/zhihu/` |
| 小红书 | 按 `community.rednote_user_id` 生成账号日报 | `.raw/community-info/rednote/` |
| 成绩（上财） | 拉 `sufe score list` TSV | `.raw/myself/scores.tsv` |

**完成门槛**：必须跑完抓取、`.raw → wiki/sources`、wiki-ingest 和 `full_collect.py --finish`，再向用户汇报：

- 每个来源新增/更新了多少原始文件；
- 新增/更新了多少 source、entity、concept、profile、question；
- 哪些来源失败或因缺登录/入参而跳过；
- dashboard 第 1–4 区哪些有变化；
- 最终结果在 `wiki/meta/dashboard.md`。

**之后每次会话结束，Stop hook 会按频率增量抓取到 `.raw/`；需要立刻完成“采集 + 沉淀 + 汇报”闭环时再次运行 `/full-collect`。**

> 如果 config 中某个来源的入参为空（如未填知乎收藏夹 URL），Codex 会跳过该项并提示补填。

## 5 引导 grill-me-study 与查看结果

- 提示运行 `/grill-me-study` 开始保研方向 grill
- 告知产物将沉淀进 `wiki/questions/` 并出现在 dashboard 第 4 区
- **明确指路**："一切信息采集与沉淀的结果最终都汇聚在 Obsidian 的 dashboard 里——**请现在就在 Obsidian 中打开 `wiki/meta/dashboard.md` 查看你的保研驾驶舱**。以后每次采集完、ingest 完或 grill 完，都优先回到 dashboard 查看更新。"
