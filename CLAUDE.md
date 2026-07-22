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

## Operations

- Ingest：把来源文件放进 `.raw/`，说 "ingest [文件名]"
- Query：直接提问；Claude 先读 hot.md → index.md → 子索引 → 具体页面
- Lint：说 "lint the wiki" 做健康检查（孤儿页、死链、过期声明）
- Archive：把冷来源移到 `.archive/` 保持 `.raw/` 干净

## 展示面板（grill 共识 2026-07-22）

- 面板 = 单个 markdown 文件 + 多段 dataview，Claudian 插件不嵌入。
- 四垂直区：最新高时效官方信息 / 官方来源信息 / 个人 SWOT / Claudian+Grill 高分问答沉淀。
- Claudian 与 grill-me 的回复沉淀进 `wiki/questions/`，frontmatter 带 `prompt_type`/`preset_slug`/`score`/`asked_at`/`answered_by`；面板只展示 `score≥4`。
- 预设提示词清单放 `wiki/meta/preset-prompts.md`。
