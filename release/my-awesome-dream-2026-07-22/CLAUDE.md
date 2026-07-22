# My Awesome Dream: LLM Wiki

Mode: C（Business/Project，定制为保研决策支持）+ E（Research）组合
Purpose: 为目标保研的大学生整合多方数据来源（个人简历等），提供数据支持与决策建议
Owner: 用户
Created: 2026-07-22

## Structure

```
vault/
├── .raw/                # 不可修改的原始材料（简历 PDF/DOCX、官网 HTML、公众号/社区原文，按指纹命名）
├── .archive/            # 冷来源归档（lint 时迁入，保持 .raw/ 干净）
├── wiki/
│   ├── index.md         # 总目录：每次 ingest 后更新
│   ├── log.md           # 追加式日志：新条目加在最上方
│   ├── hot.md           # 热缓存：最近 ~500 字上下文，每次会话先读
│   ├── overview.md      # 全局执行摘要
│   ├── sources/         # 每个 .raw 来源一页 md（type: source，正文=初步转 md 全文）
│   ├── entities/        # 所有实体统一放此（type: entity）：院校、教授、用户本人
│   ├── concepts/        # 所有概念统一放此（type: concept）：保研术语 + 推免规则
│   ├── targets/         # MOC 索引页：聚合 entity_type=org 的目标院校
│   ├── profile/         # MOC 索引页：聚合用户本人衍生页
│   ├── requirements/    # MOC 索引页：聚合 tag:保研规则 的概念
│   ├── comparisons/     # 院校/项目/策略对比分析（type: comparison）
│   ├── strategy/        # 申请策略、时间线、材料清单、风险预案（type: strategy）
│   ├── questions/       # 用户提问归档 + Claudian/grill-me 回复沉淀（type: question，带 score/prompt_type）
└── meta/            # 仪表板、健康检查报告、约定、preset-prompts 清单
│   └── meta/            # 仪表板、健康检查报告、约定
├── _templates/          # Templater 模板（source/entity/concept/comparison/strategy/question）
└── CLAUDE.md            # 本文件
```

## 物理放置约定（路 C：官方实体层 + 薄业务索引层）

- 实体页只写 `entities/`，概念页只写 `concepts/`——与 claude-obsidian 官方 Generic 对齐，使官方 `wiki-ingest`/`wiki-lint` agent 无需改造即可复用。
- `targets/`、`profile/`、`requirements/` 是 **MOC 索引页目录**，不装实体/概念页本身，只用 Bases/Dataview 聚合。
- `comparisons/`、`strategy/`、`questions/` 为独立类型目录（官方无对应，需自补模板，尤其 `strategy`）。

## Conventions

- 所有笔记使用 YAML frontmatter：type, title, status, created, updated, tags（最低要求）
- Wikilink 使用 `[[Note Name]]` 格式：文件名唯一，无需路径
- `.raw/` 存放来源材料：**永不修改**
- `wiki/index.md` 是总目录：每次 ingest 都要更新
- `wiki/log.md` 只追加：永不编辑历史条目；新条目加在文件**最上方**
- `wiki/hot.md` 是缓存不是日记：每次完全重写，控制在 500 字以内
- **社区域铁律**：zhihu-fetch / rednote-skill / wechat-article-search 三个社区 skill 的产物**一律只进 `.raw/community-info/<skill 名>/`，禁止直写 `wiki/`**；初步处理后进 `wiki/sources/`。

## Operations

- Ingest：把来源文件放进 `.raw/`，说 "ingest [文件名]"（触发 `scripts/convert_raw_to_sources.py` 把 `.raw` pending 转 `wiki/sources/` md，再走官方 wiki-ingest agent 提炼 concept/entity）
- **完整全量采集**：用户运行 `/full-collect` 或说“根据我的 config.yaml，帮我做一次全量信息采集”——按 `.claude/skills/full-collect/SKILL.md` 跑完所有已启用来源、`.raw → source → wiki-ingest` 与 `full_collect.py --finish`。**不得停在只给命令或只抓 `.raw/`**；必须汇报各来源新增/更新量、source/entity/concept/profile/question 沉淀量、失败/跳过项、dashboard 第 1–4 区变化，并提示“在 Obsidian 中打开 `wiki/meta/dashboard.md` 查看结果”。`/init` 完成配置后默认直接进入此流程，除非用户明确跳过。
- Query：直接提问；Claude 先读 hot.md → index.md → 子索引 → 具体页面
- Lint：说 "lint the wiki" 做健康检查（孤儿页、死链、过期声明 + 自补时效三层标签 current/historical/stale-suspect）
- Archive：把冷来源移到 `.archive/` 保持 `.raw/` 干净

## 数据管线（grill 共识 2026-07-22，已落地）

- **Stop hook**（`.claude/settings.json`）每次 Claude 会话结束触发 `scripts/hook_fetch.py`，读 `config.yaml` 各来源 frequency + `.last_run.yaml` 时间戳比对，命中频率则调对应抓取，产物只写 `.raw/`（async=true, 始终退出 0 不阻断停止）。
- **两跳链路**：`.raw/` 新文件 → `scripts/convert_raw_to_sources.py` 转 `wiki/sources/` md → wiki-ingest agent 提炼进 `wiki/concepts`、`wiki/entities`。
- 非真定时（受会话结束时机约束）——用户接受。

## 展示面板（grill 共识 2026-07-22）

- 面板 = 单个 markdown 文件 + 多段 dataview，Claudian 插件不嵌入。
- 四垂直区：最新高时效官方信息 / 官方来源信息 / 个人 SWOT / Claudian+Grill 高分问答沉淀。
- Claudian 与 grill-me 的回复沉淀进 `wiki/questions/`，frontmatter 带 `prompt_type`/`preset_slug`/`score`/`asked_at`/`answered_by`；面板只展示 `score≥4`。
- 预设提示词清单放 `wiki/meta/preset-prompts.md`。

## dashboard 字段对齐（grill 共识 2026-07-22）

`wiki/meta/dashboard.md` 四区 dataview 依赖以下 frontmatter 顶层字段（命名一字不差）：

- `type: source` 顶层加 `evidence_tier`（official|community）、`valid_until`、`account_or_school`
- `type: entity` / `type: concept` 顶层加 `时效标签`（current|historical|stale-suspect）、`evidence_tier`、`valid_until`、`account_or_school`
- `type: question` 顶层有 `prompt`、`prompt_type`、`score`、`asked_at`、`answered_by`
- `type: strategy` 模板见 `_templates/strategy.md`，装申请策略/时间线/材料清单/风险预案
- `wiki/profile/` 下用户本人 entity 衍生页带 `优势/劣势/机会/威胁` 四字段供 SWOT 区

## 初始化与三件物（grill 共识 2026-07-22）

- **`/init` 技能**：clone release 后首次运行，顺序：环境依赖检查 → 填 `config.yaml`（含问清所有监视网站）→ 生成骨架 → 投第一份简历触发首次 ingest → 引导 `/grill-me-study`。
- **`_templates/strategy.md`** 已建（strategy 类型，官方无、自补）。
- **`wiki/meta/dashboard.md`** 已建（四区 dataview 面板，Claudian 不嵌入）。

## 开发/使用/Release 三轨与文化（grill 共识 2026-07-22）

- 开发目录只产出模板与空骨架（无个人数据，不需排除个人数据）；使用者在外部克隆目录灌简历/跑 grill-me-study，该目录**只拉不推**，个人数据轨靠克隆目录 `.gitignore` 隔离。
- release = 开发目录打包 = 工具轨（剔除 `_dev/`）+ 空骨架 + 公共资产，**不含个人数据**。
- `wiki/` 骨架含通用保研术语种子概念页；院校/个人/规则特定内容由用户 ingest 补。
- 预装 `/claude-md-management:revise-claude-md` 与 `/skill-creator:skill-creator` 陪同 CLAUDE.md 与新 skill 的演进。
- **初始化 skill** 引导用户 clone 后初始化；**README.md** 在项目根说明初始化入口与使用方式。
