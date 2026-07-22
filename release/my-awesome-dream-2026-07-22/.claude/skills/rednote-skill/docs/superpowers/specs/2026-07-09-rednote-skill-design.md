# RedNote（小红书）Skill 设计方案

> 日期：2026-07-09
> 状态：头脑风暴完成，待进入实现计划

---

## 1. 项目概述

创建一个小红书 Skill，覆盖内容创作、图文生成、发布运营、互动评论、**数据采集**、分析复盘等能力。**v1 优先着力于数据采集**。

### 1.1 核心场景

- **运营分析** — 采集自己/竞品账号数据（笔记表现、评论互动、粉丝画像），用于内容优化和策略调整
- **舆情报警** — 监控关键词/话题，及时发现负面内容或异常数据，通过 Webhook 推送告警

### 1.2 使用模式

| 模式 | 说明 | 频率 |
|------|------|------|
| 日常按需采集 | 手动触发，搜索关键词、查看账号 | 偶尔，几十次请求 |
| 周期性批量采集 | 定时扫描一批关键词/账号，生成分析报告 | 每天/每周，几百到几千条 |
| 近实时监控 | 持续轮询关键话题，分钟级发现新增/负面 | 高频，特定主题 |

---

## 2. 技术选型

### 2.1 逆向工程基础

- 参考项目：GitHub 上 `xiaohongshutools`（纯 Python 逆向，基于 PyCryptodome，无需 Node.js/浏览器环境）
- 自行处理的加密参数：
  - Cookie 类：`a1`、`webId`、`gid`
  - 签名类：`x-s`、`x-s-common`、`x-t`
  - 追踪类：`x-b3-traceid`、`x-xray-traceid`
  - 安全类：`sec_poison_id`、`websectiga`

### 2.2 整体架构

```
┌───────────────────────────────────────┐
│ 用户  ←→  Agent (SKILL.md 引导)       │
│                │                       │
│                ▼                       │
│           rednote CLI                  │
│     (scrape / monitor / report        │
│      crypto / config)                 │
│                │                       │
│                ▼                       │
│          rednote_core                  │
│  (crypto / client / apis             │
│   report / alert)                     │
│                │                       │
│                ▼                       │
│          小红书 API                     │
│                │                       │
│                ▼                       │
│       data/reports/*.html              │
└───────────────────────────────────────┘
```

**核心思路**：Agent 参照 SKILL.md 中的场景库，匹配用户意图后直接执行 CLI 命令。所有复杂的加密、请求、解析、告警逻辑全部封装在 CLI 和内核里。**数据不落库，直接产出 HTML 报告**——自包含、可分享、打开即看。

---

## 3. Skill 设计：SKILL.md

`SKILL.md` 是本项目的核心交付物 — Agent 的操作手册。它告诉 Agent：何时触发、环境怎么搭、有哪些命令可用、常见场景怎么处理。

### 3.1 SKILL.md 结构

```markdown
---
name: rednote
description: 小红书数据采集、运营分析、舆情监控
---

# RedNote Skill

## 1. 触发条件
（用户提到小红书/RedNote/红书/笔记/种草相关数据需求时激活）

## 2. 环境安装与配置

### 安装 CLI
pip install -e .

### 验证环境
rednote crypto status

### 首次配置
rednote crypto setup --a1=xxx --webId=xxx --web_session=xxx

## 3. 可用命令速查
| 命令 | 用途 |
|------|------|
| rednote scrape search -k <关键词> | 搜索笔记 |
| rednote scrape note <note_id> | 获取笔记详情 |
| rednote scrape user <user_id> | 获取用户主页 |
| rednote scrape comments <note_id> | 获取评论 |
| rednote scrape likes <note_id> | 获取点赞列表 |
| rednote scrape follows <user_id> | 获取关注/粉丝 |
| rednote monitor start -k <关键词> | 启动舆情监控 |
| rednote monitor stop | 停止监控 |
| rednote monitor status | 查看监控状态 |
| rednote report daily | 生成运营日报 |
| rednote report sentiment | 生成舆情报告 |
| rednote crypto check | 检查加密参数有效性 |
| rednote crypto refresh | 刷新所有加密参数 |
| rednote config show | 查看当前配置 |

## 4. 场景库

### 场景1：搜索笔记
触发词：搜索/找/看看 + 关键词/话题
步骤：
  1. rednote crypto check
  2. rednote scrape search -k "<关键词>" -n <数量> -s <排序> --format html
  3. 向用户展示结果 + 报告文件路径

### 场景2：博主深度分析
触发词：分析/看看 + 博主/用户 + ID/昵称
步骤：
  1. rednote crypto check
  2. rednote scrape user <user_id>
  3. 获取该用户近期笔记 → 逐条获取互动数据
  4. rednote report daily -u <user_id> → 生成 HTML 分析报告
  5. 向用户展示报告摘要 + 文件路径

### 场景3：舆情监控
触发词：监控/追踪/关注 + 关键词/话题 + 告警/通知
步骤：
  1. rednote crypto check
  2. rednote monitor start -k "<关键词>" --webhook <url>
  3. 汇报监控已启动及当前状态

### 场景4：运营日报
触发词：日报/周报/数据报告
步骤：
  1. rednote report daily
  2. rednote report sentiment
  3. 向用户展示报告摘要 + 文件路径

## 5. 工作流程

### 一切操作的前置步骤
每次执行任何 CLI 命令前，必须先执行 rednote crypto check：
  - 参数有效 → 继续执行
  - 参数无效/缺失 → 执行 rednote crypto refresh
    - 刷新成功 → 继续执行
    - 刷新失败 → 提示用户 rednote crypto setup

## 6. 注意事项
- 请求频率：控制间隔避免触发反爬
- 加密参数有效期：约数小时，失效后需刷新
- 所有采集结果直接输出为 HTML 报告，保存在 data/reports/ 目录
```

### 3.2 场景库设计原则

| 要素 | 说明 |
|------|------|
| **触发词** | 自然语言锚点，Agent 用来匹配用户意图 |
| **命令序列** | 具体的 CLI 命令，Agent 直接执行不需要翻译 |
| **异常处理** | 461 → 刷新加密参数；限流 → 等待重试；空结果 → 扩展搜索范围 |

### 3.3 Agent 如何使用 SKILL.md

```
用户输入 "帮我搜一下最近关于护肤的热门笔记"
          │
          ▼
Agent 读取 SKILL.md
          │
          ▼
匹配场景库 → 命中"场景1：搜索笔记"
          │
          ▼
执行前置步骤：rednote crypto check
          │
          ▼
执行 CLI：rednote scrape search -k "护肤" -n 20 -s hot --format html
          │
          ▼
回报搜索结果 + data/reports/2026-07-09-search-护肤.html 路径
```

### 3.4 设计核心

- **SKILL.md 是操作手册**，不是源码。Agent 读它就知道怎么做事
- **一切走 CLI** — 所有操作通过 `rednote ...` 命令完成
- **细节在 CLI/内核里** — 加密、签名、重试、解析全部封装，SKILL.md 不解释原理
- **场景可参照** — Agent 遇到新需求时，从场景库找最接近的模板改编执行

---

## 4. CLI 设计

CLI 是 Agent 和用户的唯一操作入口。所有复杂的 API 逻辑（加密参数注入、请求重试、响应解析、告警触发）全部封装在 CLI 内部。

### 4.1 命令结构

```
rednote
├── rednote scrape ...       # 数据采集 → 输出 HTML 报告
│   ├── search              #   搜索笔记
│   ├── note                #   笔记详情
│   ├── user                #   用户资料
│   ├── comments            #   评论
│   ├── likes               #   点赞
│   └── follows             #   关注/粉丝
├── rednote monitor ...      # 舆情监控
│   ├── start               #   启动监控任务
│   ├── stop                #   停止监控
│   └── status              #   查看监控状态
├── rednote report ...       # 报告生成
│   ├── daily               #   运营日报
│   ├── sentiment           #   舆情报告
│   └── benchmark           #   竞品对比
├── rednote crypto ...       # 加密参数管理
│   ├── check               #   检查参数有效性
│   ├── refresh             #   刷新所有参数
│   ├── setup               #   首次配置加密参数
│   └── status              #   查看参数状态
└── rednote config ...       # 配置管理
    ├── set                 #   设置配置项
    └── show                #   查看当前配置
```

### 4.2 CLI 内部封装的内容

| 封装层 | 说明 |
|--------|------|
| 加密参数注入 | 每次请求自动附加 x-s、x-s-common、x-t 等签名 |
| 重试与容错 | 461 → 自动刷新参数重试；限流 → 退避等待 |
| 响应解析 | JSON 解析、错误码判断、字段标准化 |
| 报告生成 | 采集结果直接渲染为 HTML 报告（含图表、样式） |
| 告警触发 | 舆情监控结果匹配告警规则时自动推送 Webhook |
| 输出格式 | 默认 HTML 报告，同时支持 `--format json` 输出原始数据 |

### 4.3 设计原则

- CLI 是单一入口，Agent 不需要关心底层实现
- 参数设计简洁，常用值有默认（如 `-n 20`、`-s hot`）
- 默认输出 HTML 报告到 `data/reports/`，文件自包含可直接分享
- `--help` 每个子命令都有完整帮助，Agent 遇到不熟悉的子命令时可以自己查

---

## 5. 目录结构

```
rednote-skill/
├── SKILL.md                        # Skill 本体（核心交付物）
├── pyproject.toml                  # 项目配置 + CLI 入口点声明
├── rednote/                        # CLI（Python 可执行包）
│   ├── __init__.py
│   ├── __main__.py                 #   入口点（python -m rednote）
│   └── commands/                   #   子命令模块
│       ├── scrape.py               #     rednote scrape ...
│       ├── monitor.py              #     rednote monitor ...
│       ├── report.py               #     rednote report ...
│       ├── crypto.py               #     rednote crypto ...
│       └── config_cmd.py           #     rednote config ...
├── workflows/                      # 工作流（CLI 内部调用）
│   ├── search_collect.py           # 搜索+批量采集
│   ├── topic_monitor.py            # 话题近实时监控
│   ├── daily_report.py             # 运营日报编排
│   └── sentiment_scan.py           # 舆情扫描+告警
├── rednote_core/                   # 内核库
│   ├── __init__.py
│   ├── crypto/                     #   加密参数生成、校验、刷新
│   ├── client/                     #   HTTP 请求、签名注入、重试
│   ├── apis/                       #   小红书 API 接口封装
│   ├── report/                     #   报告模板 + 图表 + HTML 渲染
│   └── alert/                      #   告警规则 + Webhook
├── data/                           # 产出目录（自动生成，可 gitignore）
│   └── reports/                    #   HTML 报告
│       ├── 2026-07-09-search-护肤.html
│       └── 2026-07-09-daily.html
├── config/
│   ├── settings.yaml               # 全局配置
│   └── crypto_params.json          # 加密参数（加密存储）
└── tests/
```

---

## 6. 核心流程

### 6.1 一切操作的前置步骤

```
用户需求 → Agent 匹配场景
                │
                ▼
      1. rednote crypto check
         ├─ 参数有效 → 继续
         └─ 参数失效 → rednote crypto refresh
                          ├─ 成功 → 继续
                          └─ 失败 → 提示用户 rednote crypto setup
                │
                ▼
      2. 执行 CLI 命令 → 数据采集（内存中处理）
                │
                ▼
      3. 渲染 HTML 报告 → 写入 data/reports/
                │
                ▼
      4. 告警检查 + Webhook 推送（如有）
                │
                ▼
      5. 返回结果摘要 + 报告路径给用户
```

### 6.2 加密参数生命周期

- **存储**：敏感参数加密保存到 `config/crypto_params.json`
- **检测**：发送轻量测试请求，检查是否触发 461 安全挑战
- **刷新**：参数失效时，调用内核的逆向逻辑自动重新生成
- **Agent 的职责**：执行任何操作前先调 `rednote crypto check`，失效时先尝试 `refresh`，失败再让用户介入

### 6.3 Agent 交互方式

| 优先级 | 方式 | 示例 |
|--------|------|------|
| 1 | 自然语言 | "搜最近一周关于#护肤 的热门笔记" |
| 2 | 半结构化指令 | "采集笔记 关键词=护肤 数量=50" |
| 3 | 回退询问 | 意图不明确时追问具体参数 |

---

## 7. 报告与告警

### 7.1 HTML 报告

- 输出目录：`data/reports/`，按"日期-类型-关键词"命名
- 格式：自包含 HTML（内嵌 CSS + 图表 + 数据），可直接浏览器打开或分享
- 内容：关键指标、趋势图（matplotlib → base64 内嵌图片）、数据表格、舆情摘要
- 历史对比：Agent 需要时可读取旧的报告文件进行分析

### 7.2 舆情告警

- 规则引擎：阈值匹配 + 关键词匹配 + 趋势异常检测
- 通知方式：报告中 🚨 标注 + Webhook 推送（钉钉/飞书/企业微信）
- 频控：避免重复告警

---

## 8. v1 接口覆盖范围

| 接口域 | CLI 命令 |
|--------|------|
| 搜索 | `rednote scrape search` |
| 笔记详情 | `rednote scrape note` |
| 用户主页 | `rednote scrape user` |
| 评论+子评论 | `rednote scrape comments` |
| 点赞列表 | `rednote scrape likes` |
| 关注/粉丝 | `rednote scrape follows` |

扩展接口（v1 后续）：话题标签、推荐 feed、笔记发布、互动操作

---

## 9. 后续 Skill 扩展方向

| 阶段 | 能力 | 说明 |
|------|------|------|
| v1 | 数据采集 | 当前优先 |
| v2 | 内容创作 + 图文生成 | AI 辅助写笔记、生成配图 |
| v3 | 发布运营 | 定时发布、草稿管理、多账号 |
| v4 | 互动评论 | 自动回复、评论管理、粉丝互动 |
| v5 | 分析复盘 | 深度分析模型、运营建议引擎 |

---

## 10. 待决定事项

- [ ] 加密参数自动刷新的具体实现策略（纯 Python 还原 vs JS 执行兜底）
- [ ] 反爬策略细节（代理池规模、请求间隔、验证码处理）
- [ ] 定时任务的调度方式（系统 cron vs Python 内置调度器）
- [ ] 多账号支持（v1 是否需要？还是先单账号？）
