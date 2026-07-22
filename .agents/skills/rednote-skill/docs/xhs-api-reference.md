# 小红书 API 接口参考文档

> 基于 [RedCrack](https://github.com/Cialle/RedCrack) 逆向分析整理，供数据分析与采集模块设计参考。

---

## 目录

- [1. 认证模块](#1-认证模块)
- [2. 笔记模块](#2-笔记模块)
- [3. 评论模块](#3-评论模块)
- [4. 用户模块](#4-用户模块)（RedCrack 仅实现 4.1，4.2–4.5 需自行补充 🔧）
- [5. 加密请求头](#5-加密请求头)
- [6. Cookie 生成](#6-cookie-生成)
- [7. 数据分析场景映射](#7-数据分析场景映射)

---

## 1. 认证模块

Base URL: `https://edith.xiaohongshu.com`

### 1.1 发送验证码

```
GET /api/sns/web/v2/login/send_code
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `phone` | string | 是 | 手机号 |
| `zone` | string | 是 | 区号，默认 `"86"` |
| `type` | string | 是 | 固定 `"login"` |

**返回**：发送结果

---

### 1.2 扫码登录 — 创建二维码

```
POST /api/sns/web/v1/login/qrcode/create
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `qr_type` | int | 是 | 固定 `1` |

**返回字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.qr_id` | string | 二维码 ID |
| `data.code` | string | 二维码 code |

---

### 1.3 扫码登录 — 轮询状态

```
GET /api/sns/web/v1/login/qrcode/status
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `qr_id` | string | 是 | 二维码 ID |
| `code` | string | 是 | 二维码 code |

**返回字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.code_status` | string | `"2"` 表示扫码成功 |

---

### 1.4 风控 124 验证 — 初始化

```
POST /api/redcaptcha/v2/qr/init
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `verifyType` | string | 是 | 验证类型 |
| `verifyUuid` | string | 是 | 验证 UUID |
| `verifyBiz` | string | 是 | 验证业务 |
| `sourceSite` | string | 是 | 来源站点 |

**返回字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.rid` | string | 验证 rid |

---

### 1.5 风控 124 验证 — 轮询状态

```
POST /api/redcaptcha/v2/qr/status/query
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `verifyType` | string | 是 | 验证类型 |
| `verifyUuid` | string | 是 | 验证 UUID |
| `verifyBiz` | string | 是 | 验证业务 |
| `sourceSite` | string | 是 | 来源站点 |
| `rid` | string | 是 | 验证 rid |

**状态码**：`data.status == "4"` 表示用户已确认

---

### 1.6 获取当前用户信息

```
GET /api/sns/web/v2/user/me
```

无参数。使用登录态 Cookie。

**返回字段**（可用于数据分析）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.user_id` | string | 当前用户 ID |
| `data.nickname` | string | 昵称 |
| `data.avatar` | string | 头像 |
| `data.red_id` | string | 小红书号 |

**数据分析用途**：获取当前登录账号的基本信息，用于账号绑定校验、采集权限验证。

---

## 2. 笔记模块

### 2.1 搜索笔记

```
POST /api/sns/web/v1/search/notes
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|------|
| `keyword` | string | 是 | — | 搜索关键词 |
| `page` | int | 否 | 2 | 页码 |
| `page_size` | int | 否 | 20 | 每页条数 |
| `sort` | string | 否 | `"general"` | 排序方式：`general`(综合) / `time_descending`(最新) / `popularity_descending`(最热) |
| `note_type` | int | 否 | 0 | 笔记类型：`0`(全部) / `1`(图文) / `2`(视频) |
| `search_id` | string | 是 | — | 搜索 ID，由 `get_search_id()` 生成（base36 编码） |
| `image_formats` | list | 否 | `["jpg","webp","avif"]` | 图片格式 |
| `ext_flags` | list | 否 | `[]` | 扩展标记 |
| `geo` | string | 否 | `""` | 地理位置 |

**返回字段**（数据分析关键字段）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items[].note_card` | object | 笔记卡片 |
| `data.items[].note_card.note_id` | string | 笔记 ID |
| `data.items[].note_card.type` | string | `"normal"`(图文) / `"video"`(视频) |
| `data.items[].note_card.display_title` | string | 标题 |
| `data.items[].note_card.desc` | string | 正文摘要 |
| `data.items[].note_card.user` | object | 作者信息 |
| `data.items[].note_card.interact_info` | object | 互动数据（点赞/收藏/评论/分享数） |
| `data.items[].note_card.image_list` | array | 图片列表 |
| `data.items[].note_card.tag_list` | array | 标签列表 |
| `data.items[].note_card.time` | int | 发布时间戳 |
| `data.items[].note_card.ip_location` | string | IP 属地 |
| `data.has_more` | bool | 是否有更多 |
| `data.cursor` | string | 分页游标 |

**数据分析用途**：关键词趋势分析、竞品内容监控、热门内容发现、内容量统计。

---

### 2.2 笔记详情

```
POST /api/sns/web/v1/feed
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_note_id` | string | 是 | 笔记 ID |
| `xsec_token` | string | 是 | xsec token（从搜索/列表结果的 `xsec_token` 字段获取） |
| `xsec_source` | string | 是 | 固定 `"pc_feed"` |
| `image_formats` | list | 否 | `["jpg","webp","avif"]` |
| `extra.need_body_topic` | string | 否 | `"1"` |

**返回字段**（数据分析关键字段）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items[0].note_card` | object | 笔记完整信息 |
| `data.items[0].note_card.note_id` | string | 笔记 ID |
| `data.items[0].note_card.type` | string | 笔记类型 |
| `data.items[0].note_card.title` | string | 笔记标题 |
| `data.items[0].note_card.desc` | string | 正文内容 |
| `data.items[0].note_card.user.user_id` | string | 作者 ID |
| `data.items[0].note_card.user.nickname` | string | 作者昵称 |
| `data.items[0].note_card.user.avatar` | string | 作者头像 |
| `data.items[0].note_card.interact_info.liked_count` | int | 点赞数 |
| `data.items[0].note_card.interact_info.collected_count` | int | 收藏数 |
| `data.items[0].note_card.interact_info.comment_count` | int | 评论数 |
| `data.items[0].note_card.interact_info.share_count` | int | 分享数 |
| `data.items[0].note_card.tag_list[]` | array | 标签（含话题） |
| `data.items[0].note_card.image_list[]` | array | 图片信息 |
| `data.items[0].note_card.video` | object | 视频信息（视频笔记） |
| `data.items[0].note_card.time` | int | 发布时间戳 |
| `data.items[0].note_card.ip_location` | string | IP 属地 |
| `data.items[0].note_card.update_time` | int | 更新时间戳 |

**数据分析用途**：内容详情采集、互动数据提取、内容分类打标、正文 NLP 分析。

---

### 2.3 用户笔记列表

```
GET /api/sns/web/v1/user_posted
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|------|
| `user_id` | string | 是 | — | 用户 ID |
| `num` | int | 否 | 30 | 每次获取数量 |
| `cursor` | string | 否 | `""` | 分页游标 |
| `image_formats` | string | 否 | `"jpg,webp,avif"` | 图片格式 |
| `xsec_source` | string | 否 | `"pc_feed"` | 固定值 |

**返回字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.notes[]` | array | 笔记列表 |
| `data.has_more` | bool | 是否有更多 |
| `data.cursor` | string | 分页游标 |

**数据分析用途**：账号内容回顾、发布频率统计、内容类型分布、用户画像分析。

---

### 2.4 推荐页（HomeFeed）

```
POST /api/sns/web/v1/homefeed
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|------|
| `category` | string | 是 | — | 分类，见下方枚举 |
| `cursor_score` | string | 否 | `""` | 翻页游标（上一页返回） |
| `note_index` | int | 否 | 0 | 笔记索引（逐页递增） |
| `num` | int | 否 | 25 | 返回数量 |
| `refresh_type` | int | 否 | 1 | 刷新类型 |
| `need_num` | int | 否 | 10 | 需要数量 |
| `image_formats` | list | 否 | `["jpg","webp","avif"]` | 图片格式 |

**`category` 枚举值**：

| 值 | 中文 |
|------|------|
| `homefeed_recommend` | 推荐 |
| `homefeed.fashion_v3` | 穿搭 |
| `homefeed.food_v3` | 美食 |
| `homefeed.cosmetics_v3` | 彩妆 |
| `homefeed.movie_and_tv_v3` | 影视 |
| `homefeed.career_v3` | 职场 |
| `homefeed.love_v3` | 情感 |
| `homefeed.household_product_v3` | 家居 |
| `homefeed.gaming_v3` | 游戏 |
| `homefeed.travel_v3` | 旅行 |
| `homefeed.fitness_v3` | 健身 |

**数据分析用途**：品类内容趋势、推荐算法研究、热点内容抓取、品类竞争分析。

---

### 2.5 点赞笔记

```
POST /api/sns/web/v1/note/like
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `note_oid` | string | 是 | 笔记 ID |

**数据分析用途**：自动化互动（需谨慎使用）。

---

### 2.6 笔记曝光上报 — 进入

```
POST /api/sns/web/v1/note/metrics_report
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `note_id` | string | 是 | 笔记 ID |
| `note_type` | int | 是 | `1` 普通笔记，`2` 视频笔记 |
| `report_type` | int | 是 | `3` 表示进入 |
| `trace.request_id` | string | 是 | UUID4 请求 ID |
| `viewer.user_id` | string | 是 | 浏览者用户 ID |
| `author.user_id` | string | 是 | 作者用户 ID |
| `interaction.like` | int | 否 | `0` |
| `interaction.collect` | int | 否 | `0` |
| `interaction.comment` | int | 否 | `0` |
| `interaction.comment_read` | int | 否 | `0` |
| `note.stay_seconds` | int | 否 | `0` |
| `other.platform` | string | 否 | `"web"` |

---

### 2.7 笔记曝光上报 — 退出

```
POST /api/sns/web/v1/note/metrics_report
```

同 2.6 接口，差异字段：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `report_type` | int | 是 | `2` 表示退出 |
| `interaction.comment_read` | int | 否 | `1` |
| `note.stay_seconds` | int | 是 | 实际停留秒数 |

**数据分析用途**：模拟真实浏览行为，配合笔记详情采集。

---

## 3. 评论模块

### 3.1 获取评论列表

```
GET /api/sns/web/v2/comment/page
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|------|
| `note_id` | string | 是 | — | 笔记 ID |
| `xsec_token` | string | 是 | — | xsec token |
| `cursor` | string | 否 | `""` | 分页游标 |
| `top_comment_id` | string | 否 | `""` | 置顶评论 ID |
| `image_formats` | string | 否 | `"jpg,webp,avif"` | 图片格式 |

**返回字段**（数据分析关键字段）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.comments[]` | array | 评论列表 |
| `data.comments[].id` | string | 评论 ID |
| `data.comments[].content` | string | 评论内容 |
| `data.comments[].user_info.user_id` | string | 评论用户 ID |
| `data.comments[].user_info.nickname` | string | 评论用户昵称 |
| `data.comments[].user_info.image` | string | 评论用户头像 |
| `data.comments[].like_count` | int | 评论点赞数 |
| `data.comments[].sub_comment_count` | int | 子评论数 |
| `data.comments[].sub_comment_has_more` | bool | 子评论是否有更多 |
| `data.comments[].sub_comment_cursor` | string | 子评论分页游标 |
| `data.comments[].sub_comments[]` | array | 前几条子评论预览 |
| `data.comments[].create_time` | int | 评论时间戳 |
| `data.comments[].ip_location` | string | 评论 IP 属地 |
| `data.has_more` | bool | 是否有更多 |
| `data.cursor` | string | 分页游标 |

**数据分析用途**：评论情感分析、用户反馈收集、舆论监控、互动率计算。

---

### 3.2 获取子评论列表

```
GET /api/sns/web/v2/comment/sub/page
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `note_id` | string | 是 | 笔记 ID |
| `root_comment_id` | string | 是 | 父评论 ID |
| `num` | int | 否 | 每页数量（默认 30） |
| `cursor` | string | 否 | 分页游标 |

**返回字段**：与主评论结构一致。

**数据分析用途**：深度评论挖掘、回复链分析、用户互动网络。

---

### 3.3 发表评论

```
POST /api/sns/web/v1/comment/post
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `note_id` | string | 是 | 笔记 ID |
| `content` | string | 是 | 评论内容 |
| `at_users` | list | 否 | @用户 ID 列表 |

---

### 3.4 回复评论

```
POST /api/sns/web/v1/comment/post
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `note_id` | string | 是 | 笔记 ID |
| `content` | string | 是 | 回复内容 |
| `target_comment_id` | string | 是 | 被回复的评论 ID |
| `at_users` | list | 否 | @用户 ID 列表 |

---

### 3.5 删除评论

```
POST /api/sns/web/v1/comment/delete
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `note_id` | string | 是 | 笔记 ID |
| `comment_id` | string | 是 | 评论 ID |

---

### 3.6 点赞评论

```
POST /api/sns/web/v1/comment/like
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `note_id` | string | 是 | 笔记 ID |
| `comment_id` | string | 是 | 评论 ID（可为一/二级评论） |

---

### 3.7 取消点赞评论

```
POST /api/sns/web/v1/comment/dislike
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `note_id` | string | 是 | 笔记 ID |
| `comment_id` | string | 是 | 评论 ID |

---

## 4. 用户模块

> ⚠️ RedCrack 目前仅实现 `follow_user`，以下标注为 🔧 的接口在 RedCrack 中缺失，需自行补充。

### 4.1 关注用户

```
POST /api/sns/web/v1/user/follow
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `target_user_id` | string | 是 | 目标用户 ID |

### 4.2 取消关注用户 🔧

```
POST /api/sns/web/v1/user/unfollow
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `target_user_id` | string | 是 | 目标用户 ID |

> 该接口在 RedCrack 中未实现，需自行封装。

### 4.3 获取用户信息 🔧

```
GET /api/sns/web/v1/user/otherinfo
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `target_user_id` | string | 是 | 目标用户 ID |

**返回字段**（数据分析用途）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.user.nickname` | string | 昵称 |
| `data.user.images` | string | 头像 |
| `data.user.red_id` | string | 小红书号 |
| `data.user.desc` | string | 个人简介 |
| `data.user.gender` | int | 性别 |
| `data.user.ip_location` | string | IP 属地 |
| `data.user.follows` | int | 关注数 |
| `data.user.fans` | int | 粉丝数 |
| `data.user.interaction` | int | 获赞与收藏总数 |
| `data.user.tags` | array | 用户标签 |

**数据分析用途**：账号画像分析、粉丝/关注趋势、KOL 影响力评估。

### 4.4 获取关注列表 🔧

```
GET /api/sns/web/v1/user/followings
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|------|
| `user_id` | string | 是 | — | 目标用户 ID |
| `cursor` | string | 否 | `""` | 分页游标 |
| `page_size` | int | 否 | 12 | 每页数量 |

**数据分析用途**：社交关系图谱、KOL 关注网络分析。

### 4.5 获取粉丝列表 🔧

```
GET /api/sns/web/v1/user/fans
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|------|
| `user_id` | string | 是 | — | 目标用户 ID |
| `cursor` | string | 否 | `""` | 分页游标 |
| `page_size` | int | 否 | 12 | 每页数量 |

**数据分析用途**：粉丝画像、增长趋势、受众分析。

## 5. 加密请求头

所有 API 请求均需携带以下加密 header，由 `xhs_session` 自动注入：

| Header | 说明 | 生成位置 |
|------|------|------|
| `x-s` | 请求签名 | `header/X_S.py` |
| `x-s-common` | 通用签名参数 | `header/X_S_Common.py` |
| `x-t` | 时间戳签名 | `header/X_S.py` |
| `x-b3-traceid` | 链路追踪 ID | `header/X_B3.py` |
| `x-xray-traceid` | X-Ray 追踪 ID | `header/X_Xray.py` |
| `x-rap-param` | 风控参数（含指纹） | `header/X_Rap_Param.py` |

---

## 6. Cookie 生成

Session 初始化时自动生成的 Cookie：

| Cookie | 说明 | 生成位置 |
|------|------|------|
| `a1` | 设备标识 | `cookie/a1_and_webId.py` |
| `webId` | Web 会话标识 | `cookie/a1_and_webId.py` |
| `acw_tc` | 阿里云 WAF 令牌 | 服务端返回 → 本地解密 |
| `web_session` | 登录态 | 外部传入（或游客） |
| `sec_poison_id` | 安全标识 | 服务端返回 |
| `websectiga` | 安全 Token | `cookie/websectiga.py` |
| `gid` | 全局 ID | `cookie/gid_webprofile_data.py` |

---

## 7. 数据分析场景映射

### 7.1 内容采集场景

| 分析场景 | 需要的接口 | 数据产出 |
|------|------|------|
| 关键词趋势 | `search_notes` | 搜索结果量、内容列表 |
| 话题热度 | `search_notes` + `note_detail` | 话题笔记数、互动量趋势 |
| 竞品账号内容 | `search_user_notes` | 账号所有笔记 |
| 笔记详情采集 | `note_detail` | 完整笔记信息 |
| 品类内容分析 | `get_homefeed` | 各品类推荐内容 |
| 评论舆情 | `get_comments` + `get_sub_comments` | 评论 + 回复全文 |
| 账号画像 | `get_user_info` | 用户基础信息+粉丝/关注/获赞数 |
| 社交关系 | `get_followings` + `get_fans` | 关注+粉丝列表 |
| KOL 影响力 | `get_user_info` + `search_user_notes` | 粉丝数+内容量+互动率综合评估 |

### 7.2 互动数据维度

每条笔记可提取的分析维度：

```
笔记维度
├── 基础信息：note_id, title, desc, type, time, ip_location
├── 作者信息：user_id, nickname, avatar
├── 互动数据：liked_count, collected_count, comment_count, share_count
│   └── 衍生指标：互动率 = (赞+藏+评+分享) / 曝光量
├── 标签话题：tag_list[] → 话题聚类、话题趋势
├── 内容属性：图文/视频、是否有商品链接、是否合作
└── 评论数据：comments[] → 情感分析、关键词提取
```

### 7.3 分页策略

| 接口 | 分页方式 | 游标字段 |
|------|------|------|
| `search_notes` | page + page_size | `page` |
| `user_posted` | cursor | `cursor` |
| `get_comments` | cursor | `cursor` |
| `get_sub_comments` | cursor + num | `cursor` |
| `get_homefeed` | cursor_score | `cursor_score` |

---

## 8. 关键依赖与限制

### 8.1 `xsec_token` 传递链

```
搜索/列表结果 → note_card.xsec_token → 笔记详情/评论接口
```

几乎所有涉及具体笔记的操作（详情、评论、阅读数）都依赖 `xsec_token`，需在采集流程中保证传递链不中断。

### 8.2 请求签名机制

- **`x-s`**：核心请求签名，每次请求动态计算，依赖 `x-s-common` 和 `x-t`
- **`x-rap-param`**：风控层参数，包含设备指纹信息（CBC/ECB 加密 + Base64 编码）
- 建议在 `rednote_core/crypto/` 中独立实现签名模块，参考 RedCrack 的纯 Python 方案

### 8.3 认证方式

| 方式 | 适用场景 | 实现难度 |
|------|------|------|
| 游客模式 | 搜索、公开笔记、部分推荐页 | ✅ 低 |
| `web_session` Cookie | 登录后全功能 | ✅ 低（手动粘贴 Cookie） |
| APP 扫码登录 | 自动化登录 | ⚠️ 需补充 APP 协议 |

### 8.4 反爬注意事项

- 需要代理 IP（`create_xhs_session` 强制要求 proxy 参数）
- 请求频率需控制，建议 2-5 秒间隔
- 指纹参数（`x-rap-param`）是风控关键，RedCrack 解码部分需自行完成
- `metrics_report` 接口用于模拟真实浏览行为，有助于降低风控

---

## 附录：RedCrack 项目结构

```
RedCrack/
├── request/web/
│   ├── apis/                    # API 模块
│   │   ├── __init__.py          #   APIModule 聚合
│   │   ├── auth.py              #   认证 API
│   │   ├── note.py              #   笔记 API
│   │   ├── comments.py          #   评论 API
│   │   └── user.py              #   用户 API
│   ├── encrypt/                 # 加密模块
│   │   ├── cookie/              #   Cookie 生成
│   │   ├── header/              #   请求头签名
│   │   ├── decrypt_xs_xsc.py    #   签名解密
│   │   ├── xhs_encrypt.py       #   加密入口
│   │   └── xhs_diy_encode.py    #   自定义编码
│   ├── exceptions/              # 异常定义
│   └── xhs_session.py           # Session 核心
├── units/                       # 工具库
│   ├── base_response.py
│   └── fuck_reverse_crypto/     #   底层加密原语
│       ├── asymmetric.py
│       ├── symmetric.py
│       ├── hash_functions.py
│       ├── bitwise_operations.py
│       └── encoding.py
└── demo.py
```

---

*文档版本：v0.1 | 整理日期：2026-07-13 | 基于 RedCrack main 分支*
