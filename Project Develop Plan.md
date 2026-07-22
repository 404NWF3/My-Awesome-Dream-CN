# 这是个什么项目？

一套 Harness 系统，整合多方数据来源，为想要保研的大学牲提供数据支持与决策建议。

## 数据视角

使用 Claude Obsidian 第二大脑项目作为核心进行数据管理，https://github.com/AgriciDaniel/claude-obsidian，

### 来源层

#### 个人资产数据

这一部分以个人简历为主，将简历作为 source

如果是上海财经大学的学生，可以使用 sufe-cli 这个插件，获取个人绩点、课程分数等数据。官方仓库：https://github.com/ChengJiale150/sufe-cli。安装方式。

```
# 安装 uv
pip install uv

# 使用 uv tool 独立安装 sufe-cli 与 Playwright
uv tool install sufe-cli
uv tool install playwright

# 安装必要的运行时依赖与 Agent Skills
sufe install
```

使用 sufe-cli 的功能，更新个人绩点数据与课程分数，可以每周 hook 一下。
以上信息沉淀到 source/myself。

#### 官方数据层

监视目标院校官网的 url + 公众号，主要目标是：1. 梳理过去一年的招生时间线；2. 整理公众号信息，关注师资力量以及其项目

组织方式：

url 使用 claude code 的 playwright 插件进行网页解析与获取

用户需要配置的是目标学校的学院的官方网站或者招生网站，

公众号需要根据 Wechat Article Search 这个 skill 的规范进行配置

把资产沉淀到 source/my-dream-school/某个学院

#### 社区层

使用 https://github.com/handsomestWei/zhihu-fetch-skill 、 https://github.com/WJJ1577/RedNote-Skill 、 https://skillhub.cn/skills/wechat-article-search 这三个 skill 抓取社区信息，使用小时级别的 hook 进行社区信息获取。这三个 skill 可能是要做一些修改的，不要让他们破化我们的项目结构。在开发的时候要特别注意。

用户需要设定关键词，和前面的院校官网 url 一样，也都需要写入 config.yaml 中

把资产沉淀到 source/community-info


### 处理层

使用 [Claude Obsidian](https://github.com/AgriciDaniel/claude-obsidian) 第二大脑项目作为核心进行数据处理，将数据沉淀到 /wiki 文件夹下。具体细节 grill-me

### 展示层

这个部分一功能介绍为主，我觉得主要几个部分，一个是基于 Obsidian 的展示面板尤其是使用 Dataview 等工具进行数据与知识展示，一个是基于 Claudian 的问答（第二大脑加持），尤其是可以使用 grill-me 这个插件，在不断的 grill 中让迷茫的学子确定方向。

具体开发细节 grill-me

