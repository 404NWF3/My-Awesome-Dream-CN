# My Awesome Dream: LLM Wiki

Mode: C（Business/Project，定制为保研决策支持）+ E（Research）组合
Purpose: 为目标保研的大学生整合多方数据来源（个人简历等），提供数据支持与决策建议
Owner: 用户
Created: 2026-07-22

## Structure

```
vault/
├── .raw/                # 不可修改的原始材料（简历、成绩单、政策文件、招生通知）
├── wiki/
│   ├── index.md         # 总目录：每次 ingest 后更新
│   ├── log.md           # 追加式日志：新条目加在最上方
│   ├── hot.md           # 热缓存：最近 ~500 字上下文，每次会话先读
│   ├── overview.md      # 全局执行摘要
│   ├── sources/         # 每个 .raw 来源一页摘要
│   ├── profile/         # 个人资产：简历画像、成绩、科研、竞赛、技能
│   ├── targets/         # 目标院校/学院/项目，每个一页
│   ├── requirements/    # 本校推免规则 + 目标院校接收规则
│   ├── concepts/        # 保研术语与机制（夏令营、预推免、九推……）
│   ├── comparisons/     # 院校/项目/策略对比分析
│   ├── strategy/        # 申请策略、时间线、材料清单、风险预案
│   ├── questions/       # 用户提问的归档答案
│   └── meta/            # 仪表板、健康检查报告、约定
├── _templates/          # Templater 模板（source/entity/concept/comparison/question）
└── CLAUDE.md            # 本文件
```

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
