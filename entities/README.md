# `wiki/entities/` — 实体层（官方 Generic 通用）

本目录放**所有实体**（type: entity）：目标院校/学院/项目（`entity_type: org`）、教授（`entity_type: person`）、用户本人画像（`entity_type: person` + `tag: user-self`）。

## 为什么实体统一放这里（路 C）

claude-obsidian 官方 wiki-ingest agent 默认往 `entities/` 写，放这里 agent 无需改造即可复用。业务分区（`targets/`、`profile/`）不装实体，只用 MOC 索引页聚合本目录的实体。

- 目标院校实体 → `targets/_index.md` 聚合（`entity_type=org`）
- 用户本人画像 → `profile/_index.md` 聚合（`entity_type=person` + `user-self`）

## 模板

新建实体页用 `_templates/entity.md`。