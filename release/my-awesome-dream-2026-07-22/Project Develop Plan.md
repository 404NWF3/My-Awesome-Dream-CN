# 这是个什么项目？

一套 Harness 系统，整合多方数据来源，为想要保研的大学牲提供数据支持与决策建议。

## 数据视角

使用 Claude Obsidian 第二大脑项目作为核心进行数据管理，https://github.com/AgriciDaniel/claude-obsidian，

### 来源层

#### 数据分层契约（grill 共识 2026-07-22）

单向数据流，两层语义不同，任何 skill/抓取器都不准越层直写：

- **`.raw/`** = 抓取器吐出的**原始字节**（简历 PDF/DOCX、官网 HTML、公众号正文原文等），格式各异，**永不修改**，按内容指纹去重（已 fetch 过的不落盘 v2，只保存新内容）。证据层，可在复查时回看清洁过程。
- **`wiki/sources/`** = 初步转化为 **md** 的每来源摘要（带 frontmatter）。由 ingest 从 `.raw/` 读取后生成，是唯一可写 `wiki/` 的入口。
- `wiki/` 中的 **concept / entity** 才是从 `wiki/sources/` 提炼的精华。

**社区域铁律**：zhihu-fetch / RedNote / wechat-article-search 三个社区 skill 的产物**只准写 `.raw/`**，绝不允许直写 `wiki/`；初步处理后进 `wiki/sources/`。此约束需在**各 skill 本体说明 + CLAUDE.md 双写**。

#### 个人资产数据

这一部分以个人简历为主，将简历作为 source

如果是上海财经大学的学生，可以使用 sufe-cli 这个插件，获取个人绩点、课程分数等数据。官方仓库：https://github.com/ChengJiale150/sufe-cli。安装方式。

```
# 安装 uv
pip install uv

# 使用 uv tool 独立安装 sufe-cli 与 Playwright
uv tool install sufe-cli
uv tool install playwright

# 安装必要的运行时依赖与 Agent Skills
sufe install
```

使用 sufe-cli 的功能，更新个人绩点数据与课程分数，可以每周 hook 一下。
以上信息沉淀到 source/myself。

#### 官方数据层

监视目标院校官网的 url + 公众号，主要目标是：1. 梳理过去一年的招生时间线；2. 整理公众号信息，关注师资力量以及其项目

组织方式：

url 使用 claude code 的 playwright 插件进行网页解析与获取

用户需要配置的是目标学校的学院的官方网站或者招生网站，

公众号需要根据 Wechat Article Search 这个 skill 的规范进行配置

把资产沉淀到 source/my-dream-school/某个学院

#### 社区层

使用 https://github.com/handsomestWei/zhihu-fetch-skill 、 https://github.com/WJJ1577/RedNote-Skill 、 https://skillhub.cn/skills/wechat-article-search 这三个 skill 抓取社区信息，使用小时级别的 hook 进行社区信息获取。这三个 skill 可能是要做一些修改的，不要让他们破化我们的项目结构。在开发的时候要特别注意。

用户需要设定关键词，和前面的院校官网 url 一样，也都需要写入 config.yaml 中

把资产沉淀到 source/community-info

#### 抓取频率与失败策略（grill 共识 2026-07-22）

- **频率**：sufe 周级 / 目标院校官网**天级** / 社区小时级（三套频率本身错开，无技术冲突）
- **去重**：同一内容若已 fetch 过，不落盘 v2，只保存新内容
- **反爬**：允许 Claude Code 针对特定官网深入研究反爬并沉淀为**专属 skill / subagent**
- **公众号限频**：直接接受限制，限频当次不抓
- **社区域隔离**：见上方"社区域铁律"

#### Hook 编排（grill 共识 2026-07-22）

两跳触发链路：
1. `.raw/` 出现新文件 → 处理成 `wiki/sources/` 下的 md
2. `wiki/sources/` 出现新文件 → ingest 进 wiki 本体

#### `config.yaml`（项目根，grill 共识 2026-07-22）

分块配置，release 含空模板，用户 clone 后由初始化 skill 引导填写。

```yaml
# config.yaml — 保研 Harness 配置
user:
  name: ""                      # 本地昵称，不入 release（克隆目录填）
  school: ""                    # 本科院校，决定本校推免规则去哪 ingest
  is_sufe: false                # 是否上财学生，决定是否启用 sufe-cli 周级 hook

# 目标院校官网（天级，Playwright 解析）——可监视多个院校，列表项
watched_pages:
  - school: ""                  # 如 清华
    college: ""                 # 如 经管学院
    url: ""
    page_slug: ""               # 产物存 .raw/my-dream-school/{school}/{college}/{page_slug}/
    frequency_days: 1

# 公众号来源（wechat-article-search）
wechat:
  accounts: []                  # ["某公众号名"]
  keywords: []
  frequency_hours: 1

# 社区技能关键词（小时级）
community:
  knowledge_keywords: []        # ["保研","推免","夏令营"]
  target_keywords: []           # ["上财","复旦经济学院",...]
  frequency_hours: 1

# 产物去向（写死，用户不改——社区域铁律）
output:
  raw_dir: ".raw"               # 所有 skill 产物只进此处

# sufe-cli（上财周级）
sufe:
  enabled: false                # is_sufe=true 时改 true
  frequency_weeks: 1
```

#### 社区 skill 改造边界（grill 共识 2026-07-22）

统一铁律：三 skill 产物一律只进 `.raw/community-info/<skill 名>/`，禁止直写 `wiki/`。此约束在**各 skill 的 SKILL.md 各加一条 + CLAUDE.md 社区域铁律双写**。逐个改造动作：

| skill | 现状 | 改造动作 |
|-------|------|---------|
| **wechat-article-search** | `-o/--output` 可选 JSON，默认当前目录 | 不动代码，hook 调用时传 `-o .raw/community-info/wechat/<fingerprint>.json`；SKILL.md 加铁律一句 |
| **zhihu-fetch** | argument-hint 含"输出目录、Vault 路径"，默认写 Obsidian | 不动代码，调用时传输出目录 `.raw/community-info/zhihu/`、**禁掉写 Obsidian vault 选项**；SKILL.md 加铁律一句 |
| **rednote-skill** | 输出路径写死代码 `data/reports/` | **唯一需动代码内部**：暴露 output 路径的 CLI 参数/环境变量，强制写向 `.raw/community-info/rednote/`；SKILL.md 加铁律一句 |

#### Hook 机制（grill 共识 2026-07-22）

**Claude Code Stop hook**（写在 `.claude/settings.json`）：

```json
{
  "hooks": {
    "Stop": [
      { "matcher": "", "hooks": [{"type": "command", "command": "uv run python scripts/hook_fetch.py"}] }
    ]
  }
}
```

- Stop hook 每次 Claude 会话结束触发一次，读 `config.yaml` 各来源 `frequency_*` + 各来源 `last_run` 时间戳（存 `.raw/<source>/.last_run.yaml`）比对决定是否跑该来源抓取。
- **非真定时**：抓取时机受限于"Claude 会话结束"而非绝对时间——用户接受此现实约束。
- 产物写 `.raw/`，后续两跳（raw→source→ingest）按 Hook 编排处理。

#### 待 grill
- 初始化 skill 具体流程（下题）
- `_templates/strategy.md` 模板（下题）
- dashboard 面板四区 dataview 表达式与 frontmatter 字段对齐

#### 初始化 / strategy 模板 / dashboard 落盘（grill 共识 2026-07-22）

**初始化 skill 流程**（技能 `.claude/skills/init/SKILL.md` 已建）：
1. 环境依赖检查（Python/uv/Node+cheerio；是否上财学生→sufe-cli）。
2. 填 `config.yaml`：问清**所有需要监视的网站**（目标院校官网多个、公众号 accounts/keywords、社区关键词）。
3. 生成骨架（空 `.raw/` + `wiki/` 种子概念页 + `preset-prompts.md` 占位）。
4. 投第一份简历进 `.raw/myself/resume/` → 触发首次 ingest → 建用户本人 entity。
5. 引导运行 `/grill-me-study`。

**`_templates/strategy.md`** 已建（type: strategy，含 timeline/materials/risks/related_entity）。

**`wiki/meta/dashboard.md`** 已建（四区 dataview，Claudian 不嵌入）。

**字段对齐**（为 dataview 查得动）：
- source 顶层加 `evidence_tier`（official|community）、`valid_until`、`account_or_school`
- entity/concept 顶层加 `时效标签`（current|historical|stale-suspect）、`evidence_tier`、`valid_until`、`account_or_school`
- question 顶层 `prompt`/`prompt_type`/`score`/`asked_at`/`answered_by`
- 用户本人 entity 衍生页（`wiki/profile/`）带 `优势/劣势/机会/威胁`

#### 待 grill（后续阶段）

- 预设提示词清单具体条目（留到跑过一次 grill-me-study 后）
- release 打包机制（三轨隔离已定，打包脚本未定）
- 三个种子保研术语概念页具体写哪些术语、什么深度

#### Fetch 真实能力边界（落地共识 2026-07-22）

`scripts/hook_fetch.py` 四个 `fetch_*` 已接通真实调用（非 [TODO] 占位），但能力受各 skill 输入约束：

- **wechat-article-search**：可从 `config.wechat.keywords` 直接跑（`node search_wechat.js <kw> -o .raw/community-info/wechat/<slug>.json`）——**唯一全自动可达**。
- **sufe-cli**：跑 `uv run sufe score list`，TSV 落 `.raw/myself/scores.tsv`，需用户先 `sufe auth`。
- **zhihu-fetch / rednote-skill**：需入参（收藏夹 URL/ID、小红书 user_id），config 不提供 → hook 在缺入参时跳过并提示；用户聊天中提供链接/UID 后由 Claude 驱动抓取，产物落 `.raw/community-info/`。rednote 已暴露 `--output-dir`/`REDNOTE_OUTPUT_DIR`（见 `rednote/commands/report_cmd.py:_resolve_output_dir`）。
- **目标院校官网**：用 Playwright（Claude Code MCP 插件，不能由 bash 脚本直接调）→ hook 到频率时打"该抓"提示，由 Claude 被指向目标 URL 时用 Playwright 实抓，产物落 `.raw/my-dream-school/…`。

非真定时（受会话结束时机约束）——用户接受。

#### `.raw/` 子目录布局（grill 共识 2026-07-22）

文件名用**内容指纹**（hash），不放时间戳——文件系统层就拦住重复落盘，D 的去重天然生效。可读性放在同目录的 `<fingerprint>.meta.yaml` 里。

```
.raw/
├── myself/
│   └── resume/
│       └── <fingerprint>.pdf
├── my-dream-school/
│   └── <school-slug>/
│       └── <college-slug>/
│           └── <page-slug>/
│               └── <fingerprint>.html
└── community-info/
    ├── zhihu/
    ├── rednote/
    └── wechat/
        └── <fingerprint>.md
```

#### `.meta.yaml` 最小字段集（grill 共识 2026-07-22）

```yaml
fingerprint: <同文件名>            # 校验，防错位
source_type: resume|official|community|score
source_layer: myself|my-dream-school|community-info
fetched_at: <ISO 抓取时刻，非处理时刻>
origin:
  channel: wechat|zhihu|rednote|official-site|local-upload
  url: <原文 URL，本地上传为空>
  account_or_school: <公众号名/院校简称>
  page_slug: <官网页面 slug，社区留空>
title: <可读标题>
status: pending|processed|superseded   # processed=已产出 source；superseded=被新指纹替代
related_source_note: [[sources/某来源摘要]]  # 回链到 wiki/sources/
```

刻意不放：`raw_format`（靠文件后缀）、正文摘要（在 source 里）。

#### `wiki/sources/` 来源 md 的 frontmatter（grill 共识 2026-07-22）

每个 `.raw/` 文件处理成一篇 source md，放在 `wiki/sources/` 下，文件名用**可读 slug**（不是指纹——wiki 是给人读的）。frontmatter 对齐 `.meta.yaml` 并回指原始：

```yaml
type: source
title: <可读标题>
status: processed|stale|superseded
created: <首次处理时间>
updated: <最近一次重处理时间>
raw_fingerprint: <对应 .raw 文件指纹>   # 正向指针: source → raw
source_type: resume|official|community|score
origin:
  channel: ...
  url: ...
  account_or_school: ...
tags: [来源层标签]
```

正文 = 初步转 md 的全文（最接近原始，不做提炼）。提炼发生在下游 concept/entity 层，不在这里。

#### ingest 去重：同一原始内容重处理时（grill 共识 2026-07-22）

- `.raw/` 永不改、指纹相同不落新文件（D）。所以"同一原始内容重处理"只发生在**指纹没变的旧文件被重新 convert 成 md**（比如 convert 逻辑升级了想重跑）。
- source md **覆盖**：因为 fingerprint 相同 → 内容相同 → 产出的 source 理应相同，覆盖即"重新转换"，不留旧版 source（提炼出的 concept/entity 才是值钱的历史层，source 只是中间产物）。
- 若 fingerprint 不同（内容真变了）→ 那是"新来源"不是"重处理"：落新 `.raw/` 文件 + 旧 `.raw/` 文件 status 标 `superseded` + 产出**新** source md 页（与旧 source 并存，靠 `raw_fingerprint` 区分）。concept/entity 层由 ingest 决定如何合并新旧信息。
- 铁律边界：覆盖只发生在"同指纹重转换"这一个场景；内容变了一律走"新增"路径，绝不就地改旧 source 的正文。

#### `.archive/` 归档机制（grill 共识 2026-07-22）

- **冷判据**：`.raw/` 文件的 `status` 为 `superseded`（内容被新指纹替代了），且最近 60 天无 wikilink 新增引用。两个条件都满足才算冷——纯按时间移会被 wikilink 还在活跃引用的来源搬走，破坏跳转。
- **谁来移**：`lint the wiki` 命令负责，不在 ingest 路径上做。ingest 只管往前产，归档是单独的清理动作，避免 ingest 路径越权改 `.raw/` 布局。
- **移什么、留什么**：移 `.raw/` 的原始文件 + `.meta.yaml` 到 `.archive/<同结构>/`。**`wiki/sources/` 的 md 不移**——它是 wiki 的一部分，wikilink 要能跳到。移的是证据层，不是消化层。
- **移走后 wikilink 怎么办**：source md 的 `raw_fingerprint` 字段现在指向一个被移走的原始文件。处理：source md **前排**加一行 `> 原始已归档（fingerprint=`...`），见 .archive/`，wikilink 跳转到 source md 本身完全照旧（指 fingerprint 是元字段，不是 wikilink 目标，不受影响）。wikilink 指向的是 source md 的文件名/slug，不指向 `.raw/`，所以归档**不产生死链**。

#### 成绩数据（grill 共识 2026-07-22）

成绩单不作为独立来源。能放进简历的就放进简历；必要的单科成绩由 Claudian 在问答时主动询问用户即可。


### 处理层

使用 [Claude Obsidian](https://github.com/AgriciDaniel/claude-obsidian) 第二大脑项目作为核心进行数据处理，将数据沉淀到 /wiki 文件夹下。具体细节 grill-me

#### 与官方结构的关系（grill 共识 2026-07-22）

已核实官方仓库 Generic 模式默认目录：`sources/ entities/ concepts/ sessions/ meta/`，官方只有 source/concept/entity(+)session 几种类型，模板对应 source/concept/entity。无 `profile/targets/requirements/comparisons/strategy/questions` 这些业务目录——它们是本 vault 的定制。

**采用路 C：官方实体层 + 薄业务索引层。**

- **物理页面按官方放**：`entities/` 放所有实体（院校、教授、用户本人），`concepts/` 放所有概念（含保研规则，本质是机制）。这样 `wiki-ingest` agent 照官方逻辑直接能写 `entities/`/`concepts/`，不用改 agent。
- **业务分区用 MOC 索引页，不占物理目录装实体**：
  - `targets/_index.md`（Bases/Dataview 聚合 `entity_type=org` 的目标院校）
  - `profile/_index.md`（聚合 `entity_type=person` 中用户本人衍生页）
  - `requirements/_index.md`（聚合 `type=concept + tag:保研规则` 的规则概念）
- **`comparisons/ strategy/ questions/` 保留为独立类型**（官方没有，需补模板——尤其 `strategy` 时间线/材料清单/风险预案无处可塞）。

代价：推翻部分 initial scaffold（`targets/ profile/ requirements/` 从装实体页的物理目录改为 MOC 索引）。

#### 页面类型体系（grill 共识 2026-07-22）

| 目录 | 类型 | 模板状态 |
|------|------|---------|
| `sources/` | source | ✅ |
| `entities/` | entity（院校/教授/用户） | ✅ entity.md |
| `concepts/` | concept（术语 + 保研规则） | ✅ concept.md |
| `comparisons/` | comparison | ✅ |
| `strategy/` | **strategy（待补模板）** | ❌ 需新建 _templates/strategy.md |
| `questions/` | question | ✅ |

#### ingest 触发与去重合并（grill 共识 2026-07-22）

- **触发**：`wiki/sources/` 出现新 pending source md → **批量扫所有 pending**（非逐篇）→ 复用官方 [wiki-ingest](https://github.com/AgriciDaniel/claude-obsidian) agent 处理 → 健康检查走官方 wiki-lint agent。
- **提炼动作**：每篇 source 全量铺开——提及的每个人建 entity（尤其目标院校教授 + 其项目成员）、每个概念建 concept（尤其招生专业相关内容）。
- **去重/合并**：不同 source 提到同一实体/概念 → **合并进已有页**。若判断不能合并（是否"同一"存疑）→ **不再硬合，作为问题抛给用户**，归档到 `questions/`（这也是展示层一个板块）。
- **置信度与时效**：置信度同社区/官方分层聚合，展示时"社区归社区、官方分官方、最后综合联动"；过期招生通知在 concept/entity 层打时效标记，具体策略待 grill。

#### 待 grill（处理层）

- ingest 提炼粒度量化（官方说一次 ingest 产 8-15 页，是否照搬？）
- 置信度与时效在 frontmatter 的具体字段与加权
- "能否合并"判定失败 → 抛 question 的落库动作

#### entity/concept 层的来源追踪与时效（grill 共识 2026-07-22）

frontmatter 增量字段：

```yaml
evidence:                       # 多来源来源追踪，每个 entry 一条
  - source: [[sources/某通知]]
    evidence_tier: official|community   # 来源分层，展示时"社区归社区、官方分官方"
    confidence: high|medium|low
    captured_at: 2026-07-22
disputed: true|false            # 页内不同来源说法冲突标记
as_of: 2026-07-22               # 信息基准日（信息assume 有效基准日）
valid_until: 2027-06-30         # 可选，明确有截止事件(招生通知)时填
```

- **页内信息冲突**：页正文并列陈述不同来源说法（不取一方盖住另一方），frontmatter `disputed: true` 标记。
- **不能合并时落库**（页面级去重/合并失败）：只**记日志待用户来看**，不自动建 question 占位页。
- 展示聚合按 `evidence_tier` 分层："社区归社区、官方分官方、再来综合联动"。

#### 时效三层与 lint（grill 共识 2026-07-22）

官方 `wiki-lint` agent 只查孤儿/死链/缺口/缺交叉引用，**不识别语义时效**。自补一段时效检查挂在官方 lint 之后，产出**时效三层标签**（不是缺陷列表）：

- `current`：当季、`valid_until` 在今年内或未过 → 正常展示，最高优先级
- `historical`：`valid_until` 已过，属历史时间线 → **保留不删、不报警**，lint 标"⏳ 历史：去年通知，时间线参考"，展示层降权挪入"历史参考"分区
- `stale-suspect`：来源分层 community 且 `as_of` 很久未更新 → 标"⏳ 信息可能陈旧，建议复查"

**铁律**：historical 永远不删、不归档——去年招生时间线对预测今年节奏有价值的依据常驻 wiki。时效检查不动 `wiki/` 内容，只读 + 打标签。

#### ingest 分批与优先级（grill 共识 2026-07-22）

全量铺开 + 单次连续 ingest 设产页上限 + pending 分批：

- **单批上限**：一次连续 ingest 最多处理 N 篇 pending source（N 取 5-10，待调）。
- **每批结束**：更新 hot.md 给用户一个可消化的中间态，不一次性倒出所有 pending 导致用户面对几十条"待你判断"。
- **pending 优先级**：按来源分层 `evidence_tier` 清——official 优先于 community（官方时效更紧）。在调用官方 wiki-ingest agent 之前先排好 pending 列表再喂。
- **积压队列**：单批上限之外积压的 pending 进入下一批，靠证据分层保持 official 优先。

### 展示层

#### 展示层格局（grill 共识 2026-07-22）

- **展示面板 = 单个 markdown 文件 + 多段 dataview**，插件层用 dataview。Claudian 是独立插件，**不嵌入面板**。
- 面板四垂直区（从上到下）：

| 区块 | 内容 | 数据来源 |
|------|------|---------|
| 1 最新高时效信息 | `时效标签=current` 来自官方 | dataview 聚合 |
| 2 官方来源信息 | 官方来源其它信息（含 historical 官方时间线） | dataview 聚合 |
| 3 个人 SWOT | 用户本人优势/劣势/机会/威胁 | entity 衍生 |
| 4 Claudian/Grill 问答沉淀 | 预设提示词命中 + 自由提问评分高的 | dataview 表格 |

#### Claudian/Grill 回复沉淀与评分（grill 共识 2026-07-22）

- **沉淀位置**：Claudian 与 grill-me 的回复 → 放 `wiki/questions/`，类型 `type: question`（复用既有模板）。
- **frontmatter 补字段**：
  ```yaml
  prompt_type: preset|freeform
  preset_slug: goal-clarify|target-match|...   # preset 命中填对应 slug；freeform 留空
  score: 1-5
  asked_at: 2026-07-22
  answered_by: claudian|grill-me
  ```
- **面板第 4 区两段 dataview**（只列 `score≥4`）：
  - 4A 预设命中：`prompt_type=preset AND score>=4`
  - 4B 自由提问高分：`prompt_type=freeform AND score>=4`
  - 表格列出可读提示词/提问 + 可点击跳转的文件 wikilink（= 用户要求的"展示文件路径"）。
- **预设提示词清单**：放 `wiki/meta/preset-prompts.md` 一页，枚举所有预设提示词原文 + `preset_slug`，集中版本化；面板可加一段 dataview 展示清单引导用户去问 Claudian。
- **用户打分属性**：沉淀回复带 `score` 1-5，面板只展示高评分（阈值 4）。

## 开发 / 使用 / Release 三轨隔离（grill 共识 2026-07-22）

用户同时在三种身份间切换：**开发者**（改架构/skill，产出 release）、**使用者**（灌简历、跑 grill-me-study、积累问答）、**发布者**（打包 release 给他人，不含任何开发痕迹与个人数据）。三轨同时进行而非阶段。

### 物理隔离机制

- **两个工作目录**：当下在 **开发目录**（只产出模板与空骨架，无个人数据，故**不需要在此目录排除个人数据**）；另在外部路径维护一个 **克隆目录** 作使用者工作区。
- **G1 — 克隆目录只拉不推**：克隆目录从开发目录的 git 拉 `pull` 工具/骨架更新，自己填的个人数据**不 push** 回去，避免污染开发目录的 git。
- **个人数据隔离在克隆目录**：个人数据轨 `.gitignore` 应写在**克隆目录**（开发目录本就无这些数据，无需排除）。

### git track 策略（开发目录 = release 源）

| 类别 | 路径 | track？ |
|------|------|---------|
| 工具轨 | `.claude/skills/`（剔除 `_dev/`）、`_templates/`、CLAUDE.md | ✅ |
| 空骨架 | 空 `wiki/` 结构 + 空 `.raw/` + 空 `.archive/` | ✅ |
| 公共资产 | `wiki/meta/preset-prompts.md`、dashboard 面板、`.obsidian/` 配置（排除 workspace.json） | ✅ |
| 开发工具 | `.claude/skills/_dev/`（若有） | ❌ |
| 个人数据 | `.raw/myself/` `.raw/my-dream-school/` `.raw/community-info/` `wiki/questions/` `wiki/profile/个人画像` | ❌（本不存在于此） |

### 克隆目录额外 gitignore（隔离个人数据轨）

```
.raw/myself/
.raw/my-dream-school/
.raw/community-info/
wiki/questions/
wiki/profile/<个人画像 slug>.md
```

### Release 构成

release = 开发目录打包，内容 = 工具轨（剔除 `_dev/`）+ 空骨架 + 公共资产。**不含任何个人数据**（简历、个人目标院校、个人问答、个人画像）。

### 种子内容策略（grill 共识 2026-07-22）

release 的 `wiki/` 留**空骨架 + 通用保研术语种子概念页**（夏令营、预推免、九推等任何保研人通用的机制知识；不含任何院校/个人特定内容）。具体院校、个人、规则由用户 ingest 后补充。

## grill-me-study 设计（使用模式 grill，grill 共识 2026-07-22）

给最终用户（学子）的 grill 入口，区别于开发用的 grill-me。

- **形态 A — relentless 深挖**：一轮逐层走决策树到方向明确，不分 funnel 阶段。
- **风险与缓解**：深挖长、学子可能半途放弃 → 每轮关键问答**即时沉淀**进 `wiki/questions/`（带 `answered_by: grill-me`、`prompt_type`、`score`），中途可断点续。
- **预设提示词角色**：不是必经环节，是深挖**可选节点**——深挖到对应分支时调用 `wiki/meta/preset-prompts.md` 中对应提示词作答并沉淀，仍被展示面板第 4 区命中。

### 起手（自适应）

- **用户可见第一句**："你觉得你目前的保研竞争力如何（高/中/低）？"（不用"身份条件"——学子不易指认）
- **高** → 起 2（从"手上有什么牌"自底向上盘牌）
- **中/低** → 起 1（从"为什么读研"的动机起，先挖动机）
- **深挖中**读已 ingest 的用户 entity 客观数据校验自评（对撞 facts 与自我感知，更易挖出真实动机）。
- **不用自动读 entity 算竞争力档**（避免设定主观阈值）；判定权交回用户自评，entity 数据作校验用而非起手判据。

### 待 grill

- 起手之后的决策树骨架（relentless 深挖的分支结构）
- 即时沉淀节奏（每轮一沉淀 vs 关键节点才沉淀）
- 产物"保研方向卡片"是否生成、放哪、写进用户 entity 的哪些字段

### 决策树骨架（grill 共识 2026-07-22）

**主路径甲（中/低竞争力 → 起 1 挖动机）：**

```
Q0 保研竞争力自评 (中/低)
 └─ Q1 为什么想读研？（学术追求 / 就业出路 / 还没想清楚·主要是惯性 / 迷茫逃避）
     ├─ 学术追求 → Q2 到底想做什么研究？能否说出方向？（说不出=动机虚，回挖）
     ├─ 就业出路 → Q2 读研对目标是跳板还是必需？
     ├─ 还没想清楚·惯性 → Q2 如果不读研会怎样？是你自己在读还是他人在读？（惯性 vs 真动机对撞）
     └─ 迷茫逃避 → Q2 在逃避什么？逃避式读瑞 vs 真动机对撞
         └─ 共同汇入 Q3：在这动机下愿付什么代价？（读博年限/异地/降院校层）
             └─ Q4 目标学位浮现：学硕 / 专硕 / 直博
```

**主路径乙（高竞争力 → 起 2 盘牌）：**

```
Q0 保研竞争力自评 (高)
 └─ Q1 手上有什么牌？（科研/竞赛/绩点/英语/推荐人/软实力，逐项盘点）
     └─ Q2 这把牌打向哪？（学术导向 vs 就业导向——盘牌后仍回到动机定方向）
         └─ 合流到甲的 Q3、Q4（代价 & 目标学位）
```

**合流后：**

```
Q4 目标学位
 └─ Q5 地域偏好与城市约束（学术→导师所在；就业→目标城市产业）
     └─ Q6 目标院校层（顶尖/中流985/211/本校保底）
         └─ Q7 时间线：距推免多久？材料 deadline 倒推（对撞 ingest 官方通知时效）
             └─ Q8 强项弱项 vs 目标要求差距 → SWOT 落 user entity
                 └─ 终：保研方向卡片产出
```

### 设计判断（grill 共识 2026-07-22）

- **两条路径在 Q3/Q4 合流**：盘牌后仍回挖动机（不盘完牌就放人）。
- **"迷茫逃避"措辞软化为"还没想清楚 / 主要是惯性"**：实质 grill 不变（惯性式 vs 真动机对撞），不冲学子。
- **preset-prompts 接口点不写死在 Q6**：grill-me-study 自行判断何时调 `wiki/meta/preset-prompts.md` 中预写提示词，形态 A 自适应深挖，不硬钉。
- **产物"保研方向卡片"采用 K1 split**：定性结论（学硕/专硕、目标院校层、动机）写进 user entity 相关字段；规划性内容（时间线/材料清单/风险预案）单独成 `wiki/strategy/我的保研方向.md` 一页，链接回 entity。

### 即时沉淀节奏（grill 共识 2026-07-22）

**R2 — 关键节点才沉淀**：grill 全程对话不沉淀，只在决策树节点处（Q4 定学位、Q6 定院校层、Q8 SWOT、终：方向卡片）沉淀。一次完整 grill 产 ~5-7 条 question。理由：面板第 4 区只展示 `score≥4`，关键节点问答天然高分；逐轮沉淀产大量碎片化低价值问答会淹没面板。代价：断点续粒度粗（回最近节点），可接受。

### 预设提示词清单

`wiki/meta/preset-prompts.md` 的具体提示词收录**留到工具开发阶段逐条设计**（现在定会脱离实际——还没用过 grill-me-study 跑一次）。

