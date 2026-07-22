# RedNote CLI v1 实现设计

> 日期：2026-07-13
> 状态：已确认，待进入实现计划
> 基于：[API 参考文档](../xhs-api-reference.md) | [原始设计方案](../../../rednote-skill-design.md)

---

## 1. 架构总览

```
用户 ←→ Agent (SKILL.md)
              │
              ▼
┌───── rednote CLI (Typer) ──────────────────────┐
│  login    scrape (search/note/user/             │
│           user-notes/comments/homefeed)          │
│  config   report                                 │
└──────────────────────┬──────────────────────────┘
                       │
┌───── rednote_core ──────────────────────────────┐
│  apis/     ── 接口封装，返回 dataclass          │
│  client/   ── Session 管理、签名注入、重试       │
│  crypto/   ── 6 Header + 7 Cookie 生成           │
│  report/   ── HTML 模板 + Jinja2 渲染            │
│  config/   ── YAML 配置读写                      │
│  auth/     ── 扫码登录流程编排                   │
└──────────────────────┬──────────────────────────┘
                       │
             小红书 API (HTTPS)
```

**构建顺序**：`crypto → client → apis → auth → CLI → report → SKILL.md`

---

## 2. 技术选型

| 组件 | 选择 | 原因 |
|------|------|------|
| CLI 框架 | Typer | 原生 async、自动 help、类型安全 |
| HTTP 库 | httpx (async) | HTTP/2、代理、连接池 |
| 加密库 | pycryptodomex | RedCrack 同款，纯 Python，跨平台 |
| 报告模板 | Jinja2 + 内嵌 CSS | 自包含 HTML，单文件可分享 |
| 配置格式 | YAML (PyYAML) | 可读性好，层次化 |
| Cookie 持久化 | AES 加密 JSON | 保护敏感登录态 |
| 二维码渲染 | qrcode + 终端输出 | `rednote login` 直接显示 |

---

## 3. 加密层（crypto/）

```
rednote_core/crypto/
├── __init__.py          # 对外: sign_request(), generate_cookies()
├── header/
│   ├── x_s.py           # x-s + x-t 签名
│   ├── x_s_common.py    # x-s-common 参数
│   ├── x_b3.py          # x-b3-traceid
│   ├── x_xray.py        # x-xray-traceid
│   └── x_rap_param.py   # 风控参数（CBC/ECB 加密）
├── cookie/
│   ├── a1_webid.py      # a1 + webId 生成
│   ├── acw_tc.py        # 阿里云 WAF Token 解密
│   ├── gid.py           # gid 生成
│   └── websectiga.py    # websectiga 生成
└── primitives/          # 底层加密原语
    ├── symmetric.py     # AES-CBC, AES-ECB
    ├── asymmetric.py    # RSA
    ├── hash.py          # MD5, SHA256, HMAC
    └── encoding.py      # Base64, hex, 自定义编码
```

### 对外接口

```python
def generate_cookies() -> dict[str, str]:
    """生成本地可计算 Cookie (a1, webId, gid, websectiga)"""

def sign_request(method, url, data, cookies, headers) -> dict[str, str]:
    """签名一次请求，返回应附加的 headers"""
```

### Header 说明

| Header | 算法 | 输入 |
|--------|------|------|
| x-s | HMAC-SHA256 + 自定义编码 | url, data, x-s-common, x-t |
| x-s-common | 固定结构 + 平台参数拼接 | platform_info, a1, web_session |
| x-t | 毫秒时间戳 | `int(time() * 1000)` |
| x-b3-traceid | UUID4 hex | 随机 |
| x-xray-traceid | trace ID 格式 | 随机 + 时间戳 |
| x-rap-param | CBC 加密 + Base64 | 设备信息 JSON |

### Cookie 说明

| Cookie | 来源 | 说明 |
|--------|------|------|
| a1 | 本地计算 | 硬件指纹 Hash |
| webId | 本地计算 | UUID4 变体 |
| web_session | 扫码登录后服务端返回 | 核心登录态 |
| acw_tc | 服务端返回→本地解密 | 阿里云 WAF |
| sec_poison_id | 服务端返回 | 直接保存 |
| websectiga | 本地计算 + 服务端校验 | 安全 Token |
| gid | 本地计算 | 全局 ID |

---

## 4. HTTP 客户端层（client/）

```
rednote_core/client/
├── __init__.py          # 对外: XHSClient
├── session.py           # Session 管理（Cookie 持久化、代理配置）
├── middleware.py        # 中间件（签名注入、重试、日志）
└── exceptions.py        # 自定义异常
```

### 中间件链

```
请求 → 注入 Cookie → 注入 Headers (6签名) → 发送
                                                  │
                                             ┌────┴────┐
                                             │ 200 OK  │ → 返回
                                             │ 461     │ → 刷新→重试(1次)
                                             │ 429     │ → 退避→重试(3次)
                                             │ 471/其他│ → 抛异常
                                             └─────────┘
```

### 配置项

```yaml
# config/settings.yaml
client:
  proxy: "http://127.0.0.1:7890"   # 必填
  timeout: 30
  retry_interval: 5
  request_interval: 2
```

---

## 5. API 层（apis/） + 认证层（auth/）

### API 接口

| 函数 | 接口 | 返回 |
|------|------|------|
| search_notes() | POST /api/sns/web/v1/search/notes | SearchResult |
| get_note_detail() | POST /api/sns/web/v1/feed | NoteDetail |
| get_user_info() | GET /api/sns/web/v1/user/otherinfo | UserInfo |
| get_user_notes() | GET /api/sns/web/v1/user_posted | UserNotesResult |
| get_comments() | GET /api/sns/web/v2/comment/page | CommentResult |
| get_homefeed() | POST /api/sns/web/v1/homefeed | HomefeedResult |

每个 API 函数签名为 `async def xxx(client: XHSClient, **params) -> DataClass`。

### 认证层

```python
# 扫码登录流程
login_qrcode(client) → 创建二维码 → 终端打印 → 轮询状态 → 保存 cookie
check_login(client)  → GET /api/sns/web/v2/user/me → bool
load_cookies()       → 从加密文件加载
save_cookies(cookies)→ AES 加密保存到 config/cookies.enc
```

---

## 6. CLI 命令

```
rednote
├── rednote login                        # 扫码登录
├── rednote scrape search -k <关键词>     # 搜索笔记
├── rednote scrape note <note_id>         # 笔记详情
├── rednote scrape user <user_id>         # 用户信息
├── rednote scrape user-notes <user_id>   # 用户笔记
├── rednote scrape comments <note_id>     # 评论
├── rednote scrape homefeed -c <品类>     # 推荐页
├── rednote config show                   # 查看配置
├── rednote config set <key> <value>      # 设置配置
└── rednote report daily                  # 生成日报
```

---

## 7. 错误处理

```
RedNoteError
├── CryptoError        # 签名生成失败
├── AuthError          # 登录失效，需重新 login
├── RateLimitError     # 429 限流
├── SecurityChallenge  # 461 安全挑战（内部自动重试）
└── ParseError         # 响应解析失败
```

---

## 8. 目录结构

```
rednote-skill/
├── SKILL.md
├── PROGRESS.md              # 开发进度跟踪
├── pyproject.toml
├── rednote/                 # CLI 包
│   ├── __init__.py
│   ├── __main__.py
│   └── commands/
│       ├── login_cmd.py
│       ├── scrape.py
│       ├── report.py
│       └── config_cmd.py
├── rednote_core/            # 内核库
│   ├── __init__.py
│   ├── crypto/              # 加密（见 §3）
│   ├── client/              # HTTP 客户端（见 §4）
│   ├── apis/                # API 封装（见 §5）
│   ├── auth/                # 扫码登录
│   ├── report/              # HTML 报告
│   └── config/              # 配置管理
├── config/
│   ├── settings.yaml
│   └── cookies.enc          # 加密 Cookie（gitignore）
├── data/reports/            # HTML 报告产出
└── tests/
```

---

## 9. 实现阶段

| Phase | 内容 | 预估 |
|-------|------|------|
| Phase 1 | crypto/primitives + cookie + header | 加密层基础 |
| Phase 2 | client/ (Session, 中间件, 异常) | HTTP 客户端 |
| Phase 3 | apis/ (6个接口) + auth/ (扫码登录) | API + 认证 |
| Phase 4 | CLI 命令 + pyproject.toml | 命令行入口 |
| Phase 5 | report/ (HTML 模板 + 渲染) | 报告生成 |
| Phase 6 | SKILL.md + 端到端联调 | Skill 交付 |
| Phase 7 | 测试完善 + 文档 | 收尾 |
