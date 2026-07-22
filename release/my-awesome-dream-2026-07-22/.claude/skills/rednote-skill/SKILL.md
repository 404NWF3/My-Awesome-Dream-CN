---
name: rednote
description: 小红书数据采集、运营分析、舆情监控
env: "uv (.venv)"
---

# RedNote Skill

> **本 skill 铁律（项目约束）**：本 skill 的产物**一律只写 `.raw/community-info/rednote/`**，**禁止直写 `wiki/`**。已暴露 `--output-dir`/`-o` 参数与 `REDNOTE_OUTPUT_DIR` 环境变量（见 `rednote/commands/report_cmd.py:_resolve_output_dir`），调用时传 `-o .raw/community-info/rednote/` 或设该环境变量强制写向 `.raw/community-info/rednote/`. 初步处理后再由 ingest 进 `wiki/sources/`. 见 CLAUDE.md「社区域铁律」.

> **项目环境**：本项目使用仓库级 uv 虚拟环境（`.venv/`）。运行 `rednote` 命令请使用 `uv run rednote` 或 `.venv/Scripts/rednote`。

## 1. 触发条件

当用户提到以下关键词时激活此 Skill：
- 小红书 / RedNote / 红书 / RED / XHS
- 笔记 / 种草 / 博主 / KOL / 内容
- 搜索/采集/爬取 + 小红书相关
- 运营数据 / 舆情 / 评论分析

## 2. 环境检查

### 检查安装

```bash
uv run rednote --help
```

### 检查登录状态

```bash
uv run rednote login status
```

- 如果显示 "未登录" 或 "已过期" → 执行 `uv run rednote login`
- 如果显示 "登录状态有效" → 继续

## 3. 可用命令

| 命令 | 用途 |
|------|------|
| `rednote login` | 扫码登录，保存 Cookie |
| `rednote login status` | 检查登录状态 |
| `rednote scrape search -k <关键词>` | 搜索笔记 |
| `rednote scrape note <note_id> --xsec <token>` | 笔记详情 |
| `rednote scrape user <user_id>` | 用户信息 |
| `rednote scrape user-notes <user_id>` | 用户笔记列表 |
| `rednote scrape comments <note_id> --xsec <token>` | 获取评论 |
| `rednote scrape homefeed -c <品类>` | 推荐页（品类） |
| `rednote config show` | 查看配置 |
| `rednote report daily -u <user_id>` | 生成运营日报 |

## 4. 场景库

### 场景1：搜索笔记

**触发词**：搜索/找/看看 + 关键词/话题

```bash
uv run rednote login status
uv run rednote scrape search -k "<关键词>" -n 20 -s general
```

### 场景2：查看笔记详情

**触发词**：看看这篇笔记/详情

前置：从搜索结果获取 note_id 和 xsec_token
```bash
uv run rednote scrape note <note_id> --xsec <xsec_token>
```

### 场景3：博主分析

**触发词**：分析/看看 + 博主/用户 + ID

```bash
uv run rednote login status
uv run rednote scrape user <user_id>
uv run rednote scrape user-notes <user_id> -n 50
uv run rednote report daily -u <user_id>
```

### 场景4：查看评论

**触发词**：评论/看看评论

```bash
uv run rednote scrape comments <note_id> --xsec <xsec_token>
```

### 场景5：品类浏览

品类映射：fashion(穿搭), food(美食), cosmetics(彩妆), travel(旅行), fitness(健身), gaming(游戏), career(职场), love(情感), household(家居), movie(影视)

```bash
uv run rednote scrape homefeed -c <品类> -n 25
```

## 5. 常见问题

### Cookie 过期
```bash
uv run rednote login
# → 终端显示二维码 → 小红书 App 扫码 → 登录成功
```

### 加密错误 (461)
CLI 内部自动刷新签名并重试。如果持续失败：
1. 检查代理是否正常
2. 重新 `rednote login`

### 代理配置
编辑 `config/settings.yaml`，修改 `client.proxy` 为你的代理地址。

## 6. 安全提醒

- Cookie 加密存储在 `config/cookies.enc`
- 不要分享 cookie 文件
- 遵守小红书使用条款，仅用于个人数据分析
- 控制请求频率，建议间隔 2-5 秒
