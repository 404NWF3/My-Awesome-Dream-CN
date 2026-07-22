# My Awesome Dream · 保研决策支持 Harness

> 把"我应该保研去哪、有没有资格、什么时候该做什么"这些**靠信息差和记忆力才能答好的问题**，变成一个会自己跑、会自己记、会自己深挖你的第二大脑。
>
> 一句话：**简历、目标院校官网、公众号、社区信息自动汇入 Obsidian 知识库，Claude 据此给你决策建议，并在 grill-me-study 的 relentless 追问里帮你厘清保研方向。**

---

## 目录

- [系统架构](#系统架构)
- [系统优势](#系统优势)
- [使用方式](#使用方式)
- [第三方技术与致谢](#第三方技术与致谢)
- [项目状态](#项目状态)

---

## 系统架构

三层单向数据流，任何 skill / 脚本都**不准越层直写**——这是整个系统的地基。

```
┌─────────────────────────────────────────────────────────────┐
│  来源层  .raw/  （原始字节，永不修改，按内容指纹去重）              │
│  ├─ myself/            简历 PDF / sufe-cli 成绩                │
│  ├─ my-dream-school/   目标院校官网 HTML（天级）                 │
│  └─ community-info/    zhihu / rednote / wechat 原文（小时级）  │
│         ▲                                                    │
│         │ Stop hook 每次会话结束按频率 + 时间戳触发抓取             │
└─────────┼────────────────────────────────────────────────────┘
          │  scripts/convert_raw_to_sources.py  （第一跳）
          ▼
┌─────────────────────────────────────────────────────────────┐
│  摘要层  wiki/sources/  （初步转 md，每来源一页，带 frontmatter）   │
└─────────┬───────────────────────────────────────────────────┘
          │  claude-obsidian wiki-ingest agent  （第二跳）
          ▼
┌─────────────────────────────────────────────────────────────┐
│  精华层  wiki/                                              │
│  ├─ entities/    院校 / 教授 / 用户本人     （官方实体层）      │
│  ├─ concepts/    保研术语 + 推免规则          （官方概念层）      │
│  ├─ targets/ profile/ requirements/          （薄 MOC 索引层）  │
│  ├─ comparisons/ strategy/ questions/       （独立类型页）      │
│  └─ meta/dashboard.md                       （四区展示面板）    │
└─────────────────────────────────────────────────────────────┘
```

### 关键设计

- **`.raw/` 是证据层，永不修改**。文件名用内容指纹，已抓过的内容不会落第二份，操作系统层就拦住重复。可读元数据放在同目录 `.meta.yaml`。
- **两个工作目录隔离开发/使用**：开发目录只产出模板与空骨架（即 release 源），使用者在外部克隆目录灌简历、跑 grill、积累问答；克隆目录只拉不推，个人数据不污染项目仓库。
- **路 C：官方实体层 + 薄业务索引层**。实体页统一写 `entities/`、概念页统一写 `concepts/`（与上游 claude-obsidian 对齐，官方 `wiki-ingest` / `wiki-lint` agent 无需改造即可复用）；`targets/` `profile/` `requirements/` 不装实体，用 MOC + Dataview 聚合。
- **时效三层**：`current`（当季）/ `historical`（去年时间线，保留不删）/ `stale-suspect`（社区信息可能陈旧）。官方 lint 只查孤儿页/死链，时效语义由自补的检查段处理——**去年的招生时间线永远是财富，不是垃圾**。
- **社区 skill 铁律**：zhihu / rednote / wechat 三个社区 skill 的产物**只能进 `.raw/community-info/`**，绝不直写 `wiki/`。铁律在三个 skill 的 SKILL.md 和 CLAUDE.md 双写，把爆炸半径锁死在证据层。

### 决策流（grill-me-study）

```
   "你觉得你目前的保研竞争力如何？(高/中/低)"
            │
      ┌─────┴─────┐
      高          中/低
      │            │
   盘牌          挖动机
   （手上的牌）   （为什么读研）
      │            │
      └─────┬──────┘
         合流：愿付代价 → 目标学位
            │
   地域 → 院校层 → 时间线 → SWOT
            │
      保研方向卡片
   （定性进 entity / 规划进 strategy）
```

形态 A：relentless 深挖一轮走完决策树；只在关键节点（Q4/Q6/Q8/方向卡片）沉淀进 `wiki/questions/`，断点可续。预设提示词不是必经环节，是深挖到对应分支时可调出的弹药库。

---

## 系统优势

1. **越用越厚的个人知识资产**。`.raw/` 永不修改 + 指纹去重，每一次抓取都是净增量；去年夏令营通知到今年仍是预测今年节奏的依据，**信息只会积累，不会丢**。
2. **自动汇流，零手工搬运**。Stop hook 在你每次和 Claude 聊完结束时，按各来源自己的频率（sufe 周级 / 官网天级 / 社区小时级）决定要不要抓，产物自动进 `.raw/`、自动转 source、自动 ingest。你只管问问题。
3. **官方与社区分层聚合，不被噪音淹没**。同一件事，官方通知和社区帖子有不同可信度和时效。展示面板按 `evidence_tier` 分层展示——"社区归社区、官方分官方、最后综合联动"，谁说了什么清清楚楚。
4. **会深挖、不只回答**。迷茫的学子最缺的不是信息，是被认真追问。grill-me-study 用 relentless 决策树把"我为什么读研"追问到底，产物沉淀成方向卡片 + 高分问答进面板。
5. **结构隔离，交付干净**。开发工具、个人数据、release 骨架物理三轨分离。打包 release 给别人时，你的简历、你的目标院校、你的问答**一行都不会泄漏**。
6. **站在巨人肩膀上**。数据管理复用 claude-obsidian，社区抓取复用成熟的 zhihu/rednote/wechat skill，上财学生还复用 sufe-cli。自研的只有"保研领域层 + 调度 + 决策引导"。

---

## 使用方式

### 🚀 首次使用

Clone 后第一步：

```
/init
```

它会引导你：

1. 检查环境依赖（Python / uv / Node + cheerio；是否上财学生 → 决定是否装 sufe-cli）
2. 填写 `config.yaml`：你本人信息 + **所有需要监视的网站**（目标院校官网可配多个、公众号、社区关键词）
3. 生成空骨架（`.raw/` + `wiki/` 种子概念页 + `preset-prompts.md` 占位）
4. 提示你把第一份简历放进 `.raw/myself/resume/`，触发首次 ingest（建立你的个人画像 entity）
5. 引导运行下一步——保研方向深挖

### 日常使用

| 你想做什么 | 怎么说 |
|-----------|--------|
| 把一份原始材料纳入知识库 | 把文件放进 `.raw/`，说 `ingest <文件名>` |
| 直接问保研问题 | 直接问，Claude 先读 `hot → index → 子索引 → 具体页` |
| 深挖保研方向 | `/grill-me-study` |
| 健康检查（孤儿页/死链/时效） | `lint the wiki` |
| 查看展示面板 | 在 Obsidian 打开 `wiki/meta/dashboard.md` |

抓取是自动的：你和 Claude 每次会话结束，Stop hook 按频率决定是否抓官网/公众号/社区，新内容自动进库、自动处理、自动进面板。

### 目录速览

```
.raw/                 原始材料（永不修改）—— skill 产物只准写这一层
.archive/             冷来源归档（lint 时迁入）
wiki/                 知识库本体
  meta/dashboard.md         展示面板（四区 Dataview，Claudian 不嵌入）
  meta/preset-prompts.md    预设提示词清单
  entities/                 所有实体（院校/教授/你本人）
  concepts/                 所有概念（保研术语 + 推免规则）
  sources/                  每来源一页摘要
  questions/                Claudian/grill 回复沉淀（带评分）
config.yaml           配置（监视的网站、公众号、社区关键词）
scripts/              hook_fetch.py + convert_raw_to_sources.py
.claude/skills/       技能（init / grill-me-study / 社区 skill / sufe-* 等）
_templates/           Templater 模板
```

完整结构与约定见 [CLAUDE.md](CLAUDE.md)，设计脉络与 grill 共识见 [Project Develop Plan.md](Project%20Develop%20Plan.md)。

---

## 致谢

本系统自研的只有"保研领域层 + 调度管线 + 决策引导"，大量复用了优秀开源项目：

### 核心引擎

- **[claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian)** — 第二大脑知识库的骨架与 ingest/lint agent。本系统的 `wiki/` 结构、`wiki-ingest` / `wiki-lint` agent、路 C 的"官方实体层"理念均源于此。
- **[Claude Code](https://claude.com/claude-code)** — Harness 主体，提供 skill、hook、agent、Stop hook 调度等能力。

### 数据来源 skill

- **[zhihu-fetch](https://github.com/handsomestWei/zhihu-fetch-skill)** — 知乎收藏夹与文章抓取（API/Playwright 多级降级、Cookie 保活、批量正文与图片）。
- **[RedNote-Skill](https://github.com/WJJ1577/RedNote-Skill)** — 小红书数据采集、运营分析、舆情监控。
- **[wechat-article-search](https://skillhub.cn/skills/wechat-article-search)** — 微信公众号文章搜索（标题/摘要/发布时间/来源/链接）。
- **[sufe-cli](https://github.com/ChengJiale150/sufe-cli)** — 上海财经大学学生绩点/课程成绩/Canvas/IC 空间业务（上财学生可选）。

### Obsidian 插件（随 release 预置）

- **[Dataview](https://github.com/blacksmithgu/obsidian-dataview)** — 展示面板四区的动态聚合查询。
- **[Templater](https://github.com/SilentVoid13/Templater)** — 各类页面模板。
- **[realclaudian](https://github.com/)** — Claudian 第二大脑问答入口（独立插件，不嵌入面板）。
- **[obsidian-tasks](https://github.com/obsidian-tasks-group/obsidian-tasks)** — 任务管理。

### 开发陪伴

- **[claude-md-management](https://github.com/anthropics/claude-md-management)** — 演进 CLAUDE.md。
- **[skill-creator](https://github.com/anthropics/skill-creator)** — 制作新 skill。

### 运行时与工具链

- **Python ≥ 3.12 + [uv](https://github.com/astral-sh/uv)** — 依赖与虚拟环境。
- **Node.js + [cheerio](https://github.com/cheeriojs/cheerio)** — 公众号文章解析。
- **[Playwright](https://github.com/microsoft/playwright)** — 目标院校官网抓取与反爬。
- **[pandoc](https://github.com/jgm/pandoc)**（可选）— PDF/DOCX/HTML → markdown 转换。

> 三社区 skill 遵循本系统的"社区域铁律"——产物只进 `.raw/community-info/`，禁写 `wiki/`，避免破坏项目结构。详见各 skill 的 SKILL.md 与 CLAUDE.md。

---

## 项目状态

- **当前**：架构与骨架已落地（来源层管线、处理层 MOC、展示层面板、Stop hook 调度、种子概念页、init skill）；`hook_fetch.py` 的 fetch_* 已接通真实 CLI 调用（wechat 全自动可达，sufe 需先 auth，zhihu/rednote 缺入参由聊天驱动，官网走 Playwright）
- **待后续阶段**：
  - 预设提示词清单逐条设计（待跑过一次 grill-me-study）
  - release 打包脚本

设计与 grill 共识完整记录在 [Project Develop Plan.md](Project%20Develop%20Plan.md)。