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

#### 