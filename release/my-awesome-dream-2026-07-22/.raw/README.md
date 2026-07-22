# `.raw/` — 原始材料证据层

本目录存放抓取器/上传的**原始字节**，是整个数据流的证据层。**永不修改**已有文件。

## 数据分层契约

单向数据流：`.raw/`（原始字节）→ `wiki/sources/`（初步转 md）→ `wiki/concepts`、`wiki/entities`（提炼精华）。

任何 skill / 抓取器**都不准越层直写 `wiki/`**。

## 子目录布局

```
.raw/
├── myself/                # 个人资产（简历等）
│   └── resume/
│       └── <fingerprint>.pdf
├── my-dream-school/       # 目标院校官网抓取
│   └── <school-slug>/<college-slug>/<page-slug>/<fingerprint>.html
└── community-info/        # 社区来源（三 skill 产物只进此处）
    ├── zhihu/
    ├── rednote/
    └── wechat/
```

## 文件命名

文件名用**内容指纹**（hash），不用时间戳——文件系统层就拦住重复落盘，已 fetch 过的内容不会落 v2。可读性放在同目录的 `<fingerprint>.meta.yaml` 里（记录 slug、标题、抓取时间、来源 URL、status）。

## 谁来写

- `myself/`：用户上传简历、（上财学生）sufe-cli 产物。
- `my-dream-school/`：官网抓取（Stop hook 调度）。
- `community-info/`：zhihu-fetch / rednote-skill / wechat-article-search 三 skill——**铁律：只准写本子目录，禁写 `wiki/`**。

## 状态

- `.meta.yaml.status`：`pending`（未处理）→ `processed`（已产出 source md）→ `superseded`（被新指纹替代）。
- 归档（`lint the wiki` 时把 `superseded` 且 60 天无引用的挪进 `.archive/`）。

> release 版本中本目录为**空骨架**，用户 clone 后在此放置自己的来源材料。