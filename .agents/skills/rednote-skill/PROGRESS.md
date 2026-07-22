# RedNote CLI 开发进度

> 最后更新: 2026-07-14
> 当前阶段: ✅ v1 全部完成 — 68 个测试通过

## 总览

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 1 | 加密层 (crypto/primitives + cookie + header) | ✅ 完成 |
| Phase 2 | HTTP 客户端 (client/) | ✅ 完成 |
| Phase 3 | API + 认证 (apis/ + auth/) | ✅ 完成 |
| Phase 4 | CLI 命令 + pyproject.toml | ✅ 完成 |
| Phase 5 | 报告生成 (report/) | ✅ 完成 |
| Phase 6 | SKILL.md + 端到端联调 | ✅ 完成 |
| Phase 7 | 测试完善 + 文档 | ✅ 完成 |

---

## Phase 1: 加密层 ✅

### 1.1 项目骨架
- [x] 创建 pyproject.toml（项目配置）
- [x] 创建 rednote_core/ 包结构
- [x] 创建 rednote/ CLI 包结构
- [x] 创建 config/settings.yaml

### 1.2 底层加密原语 (primitives/)
- [x] symmetric.py — AES-CBC, AES-ECB
- [x] asymmetric.py — RSA
- [x] hash.py — MD5, SHA256, HMAC
- [x] encoding.py — Base64, hex, 自定义编码

### 1.3 Cookie 生成 (cookie/)
- [x] a1_webid.py — a1 + webId 生成
- [x] gid.py — gid 生成
- [x] websectiga.py — websectiga 生成
- [x] acw_tc.py — 阿里云 WAF Token 解密

### 1.4 Header 签名 (header/)
- [x] x_s_common.py — x-s-common 参数
- [x] x_s.py — x-s + x-t 签名
- [x] x_b3.py — x-b3-traceid
- [x] x_xray.py — x-xray-traceid
- [x] x_rap_param.py — 风控参数（CBC/ECB）

### 1.5 单元测试
- [x] primitives 测试
- [x] cookie 测试
- [x] header 测试

---

## Phase 2: HTTP 客户端 ✅

- [x] exceptions.py — 自定义异常
- [x] middleware.py — 签名注入 + 重试中间件
- [x] session.py — Session + Cookie 管理
- [x] XHSClient 集成测试

---

## Phase 3: API + 认证 ✅

### 3.1 API 封装
- [x] search.py — 搜索笔记
- [x] note.py — 笔记详情
- [x] user.py — 用户信息 + 用户笔记
- [x] comments.py — 评论 + 子评论
- [x] homefeed.py — 推荐页

### 3.2 认证
- [x] auth/login.py — 扫码登录流程
- [x] auth/persistence.py — Cookie 加密存储

---

## Phase 4: CLI 命令 ✅

- [x] pyproject.toml — [project.scripts] 入口点
- [x] rednote/__main__.py
- [x] rednote/commands/login_cmd.py
- [x] rednote/commands/scrape.py
- [x] rednote/commands/config_cmd.py
- [x] rednote/commands/report.py

---

## Phase 5: 报告生成 ✅

- [x] report/templates/ — Jinja2 模板
- [x] report/renderer.py — HTML 渲染

---

## Phase 6: SKILL.md + 联调 ✅

- [x] 编写 SKILL.md
- [x] 各命令 --help 验证

---

## Phase 7: 收尾 ✅

- [x] 集成测试 (68 个全部通过)
- [x] README 更新

---

## 恢复说明

如果会话中断，从这里继续：
1. 读取本文件，找到第一个未完成 Phase 的未勾选条目
2. 读取 `docs/superpowers/specs/2026-07-13-rednote-cli-design.md` 了解设计
3. 读取 `docs/xhs-api-reference.md` 了解 API 细节
4. 从断点继续开发
