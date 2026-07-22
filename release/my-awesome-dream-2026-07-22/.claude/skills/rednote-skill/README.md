# RedNote Skill

小红书（RedNote / Xiaohongshu）数据采集、运营分析、舆情监控 Skill — 作为 Claude Code Agent 的工具集运行。

> **状态**：v1 开发完成 ✅
> **当前进度**：Phase 1~7 全部完成 — 68 个测试通过
> **进度详情**：[PROGRESS.md](PROGRESS.md)

---

## 安装

### 方式一：从 GitHub 直接安装（推荐）

```bash
pip install git+https://github.com/WJJ1577/RedNote-Skill.git
```

锁定特定版本/分支：

```bash
pip install git+https://github.com/WJJ1577/RedNote-Skill.git@main
```

升级到最新版：

```bash
pip install --upgrade git+https://github.com/WJJ1577/RedNote-Skill.git
```

### 方式二：本地 .whl 文件安装

从仓库构建并安装：

```bash
# 克隆仓库
git clone https://github.com/WJJ1577/RedNote-Skill.git
cd RedNote-Skill

# 构建 .whl
make build

# 安装
pip install dist/rednote-0.1.0-py3-none-any.whl
```

或直接使用 `make install`（自动构建+安装）。

### 方式三：从 GitHub Release 下载 .whl

前往 [Releases](https://github.com/WJJ1577/RedNote-Skill/releases) 页面，下载最新 `.whl` 文件后安装：

```bash
pip install rednote-0.1.0-py3-none-any.whl
```

> **开发模式**（代码修改即时生效，无需重新安装）：
> ```bash
> pip install -e .
> ```

安装完成后，在任意目录都可以直接使用：

```bash
rednote --help
rednote login
rednote scrape search -k "关键词"
```

---

## 项目概述

本项目创建一个 Claude Code Skill，通过 CLI 封装小红书 API 的逆向工程、请求签名、数据采集和报告生成，让 Agent 能够：

- **运营分析** — 采集自己/竞品账号数据，自动生成 HTML 分析报告
- **舆情监控** — 监控关键词/话题，异常内容通过 Webhook 推送告警
- **按需采集** — 手动触发搜索、查看账号、获取评论互动等

## 使用模式

| 模式 | 说明 | 频率 |
|------|------|------|
| 日常按需采集 | 手动触发，搜索关键词、查看账号 | 偶尔，几十次请求 |
| 周期性批量采集 | 定时扫描关键词/账号，生成分析报告 | 每天/每周，几百到几千条 |
| 近实时监控 | 持续轮询关键话题，分钟级发现异常 | 高频，特定主题 |

## 架构一览

```
用户 ←→ Agent (SKILL.md 引导)
              │
              ▼
         rednote CLI
   (login / scrape / report
    config)
              │
              ▼
        rednote_core
(crypto / client / apis
 auth / report / config)
              │
              ▼
        小红书 API
              │
              ▼
     data/reports/*.html
```

**核心思路**：SKILL.md 是 Agent 的操作手册，所有复杂逻辑封装在 CLI 和内核中，Agent 只负责匹配用户意图 → 执行命令 → 展示结果。

## 目录结构

```
rednote-skill/
├── SKILL.md                     # Skill 本体（核心交付物）
├── PROGRESS.md                  # 开发进度跟踪
├── pyproject.toml               # 项目配置 + CLI 入口点
├── rednote/                     # CLI 命令包
│   └── commands/                #   login, scrape, report, config
├── rednote_core/                # 内核库
│   ├── crypto/                  #   加密参数生成与签名
│   │   ├── primitives/          #     底层加密原语 (AES, RSA, HMAC, Base64)
│   │   ├── cookie/              #     Cookie 生成 (a1, webId, gid, websectiga)
│   │   └── header/              #     Header 签名 (x-s, x-s-common, x-t, x-b3, x-ray, x-rap-param)
│   ├── client/                  #   HTTP 客户端（Session, 签名注入, 重试, 代理）
│   ├── apis/                    #   小红书 API 接口封装
│   ├── auth/                    #   扫码登录流程编排
│   ├── report/                  #   报告模板 + HTML 渲染
│   │   └── templates/           #     base.html, daily.html, search.html
│   └── config/                  #   配置管理
├── config/                      # 配置文件
│   ├── settings.yaml            #   全局配置
│   └── cookies.enc              #   加密 Cookie（gitignore）
├── data/reports/                # HTML 报告产出
├── docs/                        # 设计文档 + API 参考
└── tests/
```

## v1 CLI 命令

| 命令 | 用途 |
|------|------|
| `rednote login` | 扫码登录，自动保存 Cookie |
| `rednote scrape search -k <关键词>` | 搜索笔记 |
| `rednote scrape note <note_id>` | 笔记详情 |
| `rednote scrape user <user_id>` | 用户信息 |
| `rednote scrape user-notes <user_id>` | 用户笔记列表 |
| `rednote scrape comments <note_id>` | 评论+子评论 |
| `rednote scrape homefeed -c <品类>` | 品类推荐页 |
| `rednote config show` | 查看当前配置 |
| `rednote config set <key> <value>` | 设置配置 |
| `rednote report daily` | 生成运营日报 |

## v1 接口覆盖

| 接口 | 命令 | API |
|------|------|-----|
| 扫码登录 | `rednote login` | `qrcode/create` → `qrcode/status` → 保存 web_session |
| 搜索笔记 | `rednote scrape search` | `POST /api/sns/web/v1/search/notes` |
| 笔记详情 | `rednote scrape note` | `POST /api/sns/web/v1/feed` |
| 用户信息 | `rednote scrape user` | `GET /api/sns/web/v1/user/otherinfo` |
| 用户笔记 | `rednote scrape user-notes` | `GET /api/sns/web/v1/user_posted` |
| 评论 | `rednote scrape comments` | `GET /api/sns/web/v2/comment/page` + `sub/page` |
| 推荐页 | `rednote scrape homefeed` | `POST /api/sns/web/v1/homefeed` |

### 认证流程

```
rednote login
  → 生成本地 Cookie (a1, webId, gid, websectiga)
  → 创建二维码 (POST qrcode/create)
  → 终端显示二维码 (qrcode 库)
  → 轮询扫码状态 (GET qrcode/status, 每2秒)
  → 扫码成功 → 提取 web_session → AES 加密保存
```

### 加密体系

**6 个请求签名 Header**：`x-s`, `x-s-common`, `x-t`, `x-b3-traceid`, `x-xray-traceid`, `x-rap-param`

**7 个 Cookie**：`a1`, `webId`, `acw_tc`, `web_session`, `sec_poison_id`, `websectiga`, `gid`

所有加密逻辑纯 Python 实现（基于 pycryptodomex），参考 [RedCrack](https://github.com/Cialle/RedCrack) 逆向分析。

## 关键依赖与限制

- **代理 IP 必填** — 小红书 API 强制要求非中国大陆 IP 代理
- **请求频率控制** — 建议 2-5 秒间隔，避免触发反爬
- **xsec_token 传递链** — 搜索→详情→评论，必须保持
- **Cookie 有效期** — web_session 约数小时到数天，失效后需重新 `rednote login`

## 技术栈

- **语言**：Python
- **CLI 框架**：Typer
- **HTTP**：httpx (async)
- **加密**：pycryptodomex（纯 Python 逆向）
- **报告**：Jinja2 + 自包含 HTML（内嵌 CSS + 图表）
- **二维码**：qrcode 库
- **参考项目**：[RedCrack](https://github.com/Cialle/RedCrack)

## 后续路线

| 阶段 | 能力 |
|------|------|
| v1 | 数据采集 |
| v2 | 内容创作 + 图文生成 |
| v3 | 发布运营（定时发布、多账号） |
| v4 | 互动评论管理 |
| v5 | 深度分析复盘 |

## 文档

- [完整设计方案](rednote-skill-design.md)（原始头脑风暴）
- [实现设计 Spec](docs/superpowers/specs/2026-07-13-rednote-cli-design.md)
- [API 接口参考](docs/xhs-api-reference.md)
- [开发进度](PROGRESS.md)

## 许可

Private — 仅供个人使用
