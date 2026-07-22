---
name: rednote
description: 小红书数据采集、运营分析、舆情监控
---

# RedNote Skill

## 1. 触发条件

当用户提到以下关键词时激活此 Skill：
- 小红书 / RedNote / 红书 / RED / XHS
- 笔记 / 种草 / 博主 / KOL / 内容
- 搜索/采集/爬取 + 小红书相关
- 运营数据 / 舆情 / 评论分析

## 2. 环境检查

### 检查安装

```bash
cd <project_dir> && PYTHONPATH=. python3 -m rednote --help
```

### 检查登录状态

```bash
PYTHONPATH=. python3 -m rednote login status
```

- 如果显示 "未登录" 或 "已过期" → 执行 `PYTHONPATH=. python3 -m rednote login`
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
cd <project_dir>
PYTHONPATH=. python3 -m rednote login status
PYTHONPATH=. python3 -m rednote scrape search -k "<关键词>" -n 20 -s general
```

### 场景2：查看笔记详情

**触发词**：看看这篇笔记/详情

前置：从搜索结果获取 note_id 和 xsec_token
```bash
PYTHONPATH=. python3 -m rednote scrape note <note_id> --xsec <xsec_token>
```

### 场景3：博主分析

**触发词**：分析/看看 + 博主/用户 + ID

```bash
PYTHONPATH=. python3 -m rednote login status
PYTHONPATH=. python3 -m rednote scrape user <user_id>
PYTHONPATH=. python3 -m rednote scrape user-notes <user_id> -n 50
PYTHONPATH=. python3 -m rednote report daily -u <user_id>
```

### 场景4：查看评论

**触发词**：评论/看看评论

```bash
PYTHONPATH=. python3 -m rednote scrape comments <note_id> --xsec <xsec_token>
```

### 场景5：品类浏览

品类映射：fashion(穿搭), food(美食), cosmetics(彩妆), travel(旅行), fitness(健身), gaming(游戏), career(职场), love(情感), household(家居), movie(影视)

```bash
PYTHONPATH=. python3 -m rednote scrape homefeed -c <品类> -n 25
```

## 5. 常见问题

### Cookie 过期
```bash
PYTHONPATH=. python3 -m rednote login
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
