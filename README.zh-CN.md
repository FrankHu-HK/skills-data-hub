<div align="center">
  <img src="banner.svg" alt="技能数据看板横幅" width="100%" />
  <h1>技能数据看板（Skills Data Hub）</h1>
  <p><b>SkillHub 开发者实时数据分析面板</b> —— 下载量、测评分数、竞品搜索、类目热度，统一约 50 秒刷新。</p>
</div>

<p align="center">
  <a href="https://github.com/FrankHu-HK/skills-data-hub/stargazers"><img src="https://img.shields.io/github/stars/FrankHu-HK/skills-data-hub?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/FrankHu-HK/skills-data-hub/network/members"><img src="https://img.shields.io/github/forks/FrankHu-HK/skills-data-hub?style=flat-square" alt="Forks"></a>
  <a href="https://github.com/FrankHu-HK/skills-data-hub/issues"><img src="https://img.shields.io/github/issues/FrankHu-HK/skills-data-hub?style=flat-square" alt="Issues"></a>
  <a href="https://github.com/FrankHu-HK/skills-data-hub/blob/master/LICENSE"><img src="https://img.shields.io/github/license/FrankHu-HK/skills-data-hub?style=flat-square" alt="License"></a>
  <a href="https://img.shields.io/github/last-commit/FrankHu-HK/skills-data-hub?style=flat-square"><img src="https://img.shields.io/github/last-commit/FrankHu-HK/skills-data-hub?style=flat-square" alt="Last commit"></a>
  <a href="https://github.com/sponsors/FrankHu-HK"><img src="https://img.shields.io/badge/Sponsor-%E2%9D%A4-brightgreen" alt="Sponsor"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/形态-Web%20面板-0ea5e9?style=flat-square" alt="Web">
  <img src="https://img.shields.io/badge/API%20Key-无需-22c55e?style=flat-square" alt="No API key">
  <img src="https://img.shields.io/github/languages/top/FrankHu-HK/skills-data-hub?style=flat-square" alt="Language">
</p>

<p align="center">
  [简体中文] | <a href="README.md">English</a>
</p>

---

## 技能数据看板是什么？

面向 **SkillHub 创作者的实时决策中心**。它将下载量、收藏量、测评分数、市场数据、类目热度统一在约 50 秒轮询内，并叠加全平台竞品搜索与蓝海/红海策略提示，汇成一块可常驻第二块屏幕的看板（电脑或平板，同 Wi-Fi 即可）。

## 为什么选它？

### 痛点

- 做技能只是一半，知道它 **表现如何** 是另一半。
- SkillHub 的数字分散，容易误读。
- 竞品动向与类目趋势，不持续手动盯就看不见。

### 核心思路：一块统一看板

输入一次 SkillHub 用户 ID，看板自行保持新鲜，把原始数字变成 **下一步做什么、迭代什么**。

## 核心特性

- **约 50 秒统一实时刷新** —— 下载、收藏、测评分数、版本时间、测评报告时间、市场数据、类目热度一并轮询。
- **全平台竞品搜索** —— 关键词同时匹配 **名称 + 介绍**，核心词/排除词双重过滤。双维度排名：**下载量 TOP10** 与 **最新上传 TOP10**。
- **类目热度排行** —— 蓝海/红海识别 + 方向建议。
- **版本 ↔ 测评闭环** —— 每张卡片显示 `vX 发布 N 天后 → 测评 Y 分`，验证迭代是否真的有效。
- **环比增长** —— 各项指标的昨日环比变化。
- **精致体验** —— 翻页数字动画、深色科技风 UI、跨设备实时展示。
- **零配置检测** —— 自动识别你的技能；可选 `config.json` 覆盖，无需改代码。

## 快速开始

### 环境要求

- Python 3.10+（用于自带服务）**或** 直接浏览器打开静态看板。
- 一个 SkillHub 用户 ID。

### 运行

```bash
# 方式 A：静态看板（无需服务）
open dashboard.html

# 方式 B：本地服务 + 实时刷新
python server.py
# 然后访问打印出的本地地址
```

在界面输入 SkillHub 用户 ID，看板开始轮询。

## 开发

`server.py` 提供服务，`config.json` 存放可选覆盖，`chart.umd.min.js` 为图表依赖。改动刷新或排名逻辑前请先读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 路线图

见 [ROADMAP.md](ROADMAP.md)。

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。欢迎新的排名信号与更清晰的策略提示。

<a href="https://github.com/FrankHu-HK/skills-data-hub/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=FrankHu-HK/skills-data-hub" />
</a>

## 💖 赞助

如果看板帮你做出更好的技能或发现蓝海，欢迎赞助其开发。赞助让它保持 **免费、持续迭代**。

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-brightgreen)](https://github.com/sponsors/FrankHu-HK)

## 许可证

[MIT](LICENSE) — Copyright 2026 Frank Hu（胡景堃）。
