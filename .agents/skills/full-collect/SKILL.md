---
name: full-collect
description: 按 config.yaml 执行一次完整的保研信息采集、source 转换、wiki-ingest 沉淀与结果汇报。用户说“全面/全量信息采集”“采集所有来源”“更新全部情报”，调用 /full-collect，或 /init 完成配置后首次采集时使用。
---

# 全量信息采集

把“抓取 → 转 source → wiki-ingest → 汇报 → 打开 dashboard”作为一次完整操作。不要只把命令交给用户，也不要在抓完 `.raw/` 后提前结束。

## 执行流程

1. 读取 `config.yaml`，列出已启用来源与缺少的必要入参。空入参来源允许跳过，但要在最终汇报中说明。
2. 运行 `uv run python scripts/full_collect.py`，强制尝试所有已启用来源并转换 pending 原始文件。
3. 从输出或 `.full_collect_state.json` 取得本轮新增/更新的 source 列表。
4. 若列表非空，立即按 wiki-ingest 的 Batch Ingest 流程处理这些 source；用户调用本技能即视为已确认。提炼 entity / concept，更新 `wiki/index.md`、`wiki/hot.md`、`wiki/log.md`，保持 `.raw/` 不可修改。
5. wiki-ingest 完成后运行 `uv run python scripts/full_collect.py --finish`。
6. 用最终统计结果汇报，不得只说“完成了”。

## 必须汇报

- 官网、公众号、知乎、小红书、个人材料/成绩各自新增和更新了多少原始文件。
- source / entity / concept / profile / question 各自新增和更新了多少。
- 哪些来源失败或跳过，以及缺配置、缺登录或抓取错误的补救方法。
- dashboard 第 1–4 区哪些有变化；不要把未命中过滤条件的社区 source 说成已显示。
- 明确说“请在 Obsidian 中打开 `wiki/meta/dashboard.md`”。

以这句话收尾：

> 以后每次完成采集、ingest 或 grill 后，都优先打开 `wiki/meta/dashboard.md` 查看你的保研驾驶舱。

某个来源失败时继续其他来源。没有新 source 时仍运行 `--finish`。wiki-ingest 未完成时不要宣称“沉淀完成”。
