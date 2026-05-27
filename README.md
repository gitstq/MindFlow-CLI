<p align="center">
  <a href="#简体中文">简体中文</a> | <a href="#繁體中文">繁體中文</a> | <a href="#english">English</a>
</p>

---

<!-- language-anchor:zh-CN -->

# 🧠 MindFlow-CLI

<p align="center">
  <b>轻量级 AI 知识工作流自动化引擎</b><br>
  <i>纯 Python 实现 · 零外部依赖 · 开箱即用</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/python-3.8%2B-yellow" alt="Python">
  <img src="https://img.shields.io/badge/tests-151%20passed-success" alt="Tests">
  <img src="https://img.shields.io/badge/code-8300%2B%20lines-orange" alt="Code">
</p>

---

## 🎉 项目介绍

**MindFlow-CLI** 是一款面向知识工作者和开发者的**命令行知识管理工具**，它将知识片段管理、智能搜索、AI 工作流编排和模板化输出融为一体，帮助你在终端中高效完成从「信息采集」到「知识沉淀」的全链路闭环。

无论你是需要整理研究笔记的研究员、梳理会议纪要的项目经理，还是希望用 AI 加速日常工作的开发者，MindFlow-CLI 都能成为你得心应手的效率利器。

### 🌟 为什么选择 MindFlow-CLI？

- **🪶 轻量极致** — 纯 Python 实现，零外部依赖，`pip install` 即可使用
- **🧩 模块化设计** — 知识管理、搜索引擎、工作流引擎、模板系统各司其职，可独立运作也可无缝协作
- **🤖 AI 原生** — 内置多 LLM 集成，支持 OpenAI / Anthropic / Ollama，让 AI 真正融入你的知识工作流
- **📊 终端美学** — 精心打磨的 TUI 交互式仪表盘，让命令行也能赏心悦目
- **🧪 质量可靠** — 8300+ 行代码，151 个测试全部通过，覆盖核心业务逻辑

---

## ✨ 核心特性

### 📝 知识片段管理
完整的 CRUD 操作，支持**标签分类**与**全文搜索**，让你的每一条知识都有迹可循。

```bash
# 添加一条知识片段
mindflow add --title "Python 装饰器" --content "装饰器是Python中用于修改函数行为的语法糖..." --tags python,语法

# 查看所有知识片段
mindflow list

# 搜索知识
mindflow search "装饰器"
```

### 🔗 DAG 工作流引擎
基于**有向无环图（DAG）**的工作流编排引擎，支持条件分支和并行执行，让复杂的知识处理流程变得清晰可控。

```bash
# 运行工作流
mindflow workflow run research_pipeline

# 查看可用工作流
mindflow workflow list
```

### 🤖 多 LLM 集成
统一的接口层对接 **OpenAI / Anthropic / Ollama**，一处配置、多处调用，灵活切换模型供应商。

```bash
# 配置 LLM
mindflow config set llm.provider openai
mindflow config set llm.model gpt-4
```

### 🔍 TF-IDF + BM25 混合搜索引擎
自研混合搜索引擎，融合 **TF-IDF** 和 **BM25** 算法，原生支持中英文双语检索，精准定位你需要的知识。

```bash
# 全文搜索
mindflow search "机器学习入门"

# 按标签过滤
mindflow search --tags AI,教程
```

### 📋 模板系统
内置 **6 个精心设计的预设模板**，覆盖常见知识工作场景：

| 模板名称 | 适用场景 |
|---------|---------|
| 📚 研究整理 | 学术论文、技术调研的结构化整理 |
| 📝 会议纪要 | 会议要点提炼与行动项追踪 |
| 📖 学习笔记 | 课程笔记、读书笔记的系统化记录 |
| 📂 项目文档 | 项目架构、API 文档的规范化输出 |
| 🔎 代码审查 | Code Review 要点与改进建议 |
| 📊 周报生成 | 一周工作总结与下周计划 |

```bash
# 查看可用模板
mindflow template list

# 应用模板
mindflow template apply 研究整理 --title "大模型技术调研"
```

### 📊 TUI 交互式仪表盘
基于 **curses** 的终端交互界面，实时展示知识库统计、标签分布、近期活动等关键信息。

```bash
# 启动仪表盘
mindflow tui
```

### 📤 多格式导出
支持导出为 **JSON / Markdown / HTML** 三种格式，方便分享与二次加工。

```bash
# 导出为 Markdown
mindflow export markdown --output notes.md

# 导出为 HTML
mindflow export html --output report.html

# 导出为 JSON
mindflow export json --output data.json
```

### 💾 SQLite 存储引擎
内置 **SQLite** 持久化方案，零配置开箱即用，数据安全可靠，支持百万级知识片段的高效存储与检索。

---

## 🚀 快速开始

### 📋 环境要求

- **Python** >= 3.8
- **操作系统**：Windows / macOS / Linux（跨平台支持）

### 🔧 安装

```bash
# 从 PyPI 安装（推荐）
pip install mindflow-cli

# 或从源码安装
git clone https://github.com/gitstq/MindFlow-CLI.git
cd MindFlow-CLI
pip install -e .
```

### ⚡ 三步上手

```bash
# 1️⃣ 初始化知识库
mindflow init

# 2️⃣ 添加第一条知识
mindflow add --title "我的第一条知识" --content "MindFlow-CLI 让知识管理变得简单高效！" --tags 入门

# 3️⃣ 搜索与查看
mindflow search "知识"
mindflow list
```

### 🎯 快速体验工作流

```bash
# 创建一个研究工作流
mindflow workflow create research_flow

# 运行工作流
mindflow workflow run research_flow

# 查看运行结果
mindflow stats
```

---

## 📖 详细使用指南

### 📝 知识片段操作

```bash
# ➕ 添加知识片段
mindflow add --title "标题" --content "内容" --tags "标签1,标签2"

# 📋 列出所有知识片段
mindflow list
mindflow list --tags python          # 按标签过滤
mindflow list --limit 10            # 限制显示数量

# 🔍 搜索知识片段
mindflow search "关键词"
mindflow search "关键词" --tags AI   # 组合搜索

# 👁️ 查看知识片段详情
mindflow show <id>

# 🗑️ 删除知识片段
mindflow delete <id>

# 🏷️ 标签管理
mindflow tags                       # 查看所有标签
mindflow tags --sort count          # 按使用次数排序
```

### 🔗 工作流管理

```bash
# 📋 查看工作流列表
mindflow workflow list

# ➕ 创建工作流
mindflow workflow create <name>

# 🚀 运行工作流
mindflow workflow run <name>

# 📊 查看工作流执行历史
mindflow workflow run <name> --history
```

### 📋 模板使用

```bash
# 📋 查看可用模板
mindflow template list

# 🎯 应用模板生成内容
mindflow template apply <模板名> --title "标题"
```

### 📤 导出功能

```bash
# 导出为不同格式
mindflow export json --output data.json
mindflow export markdown --output notes.md
mindflow export html --output report.html

# 按标签筛选导出
mindflow export markdown --tags "AI,研究" --output ai_research.md
```

### ⚙️ 配置管理

```bash
# 查看当前配置
mindflow config

# 设置配置项
mindflow config set llm.provider openai
mindflow config set llm.model gpt-4
mindflow config set llm.api_key sk-xxx

# 查看统计信息
mindflow stats
```

---

## 💡 设计思路与迭代规划

### 🏗️ 架构设计理念

MindFlow-CLI 遵循以下核心设计原则：

1. **单一职责** — 每个模块只做一件事，做到极致（存储引擎只管存取，搜索引擎只管检索）
2. **接口抽象** — 通过统一的抽象层对接不同 LLM 供应商，切换模型无需改动业务代码
3. **渐进增强** — 核心功能零依赖可用，AI 能力按需开启
4. **数据本地化** — 所有数据存储在本地 SQLite，隐私安全有保障

### 📁 项目结构

```
MindFlow-CLI/
├── mindflow_cli/          # 核心源码
│   ├── cli.py             # 命令行入口
│   ├── storage.py         # SQLite 存储引擎
│   ├── search_engine.py   # TF-IDF + BM25 搜索引擎
│   ├── workflow_engine.py # DAG 工作流引擎
│   ├── llm_client.py      # 多 LLM 统一客户端
│   ├── template_manager.py# 模板管理器
│   ├── exporter.py        # 多格式导出器
│   ├── tui.py             # TUI 交互式仪表盘
│   ├── models.py          # 数据模型定义
│   ├── config.py          # 配置管理
│   └── utils.py           # 工具函数
├── tests/                 # 测试套件（151 个测试）
├── pyproject.toml         # 项目配置
├── setup.py               # 安装配置
└── LICENSE                # MIT 许可证
```

### 🗺️ 迭代规划

| 阶段 | 内容 | 状态 |
|------|------|------|
| v1.0 | 核心功能：知识管理 + 搜索 + 工作流 + 模板 + 导出 | ✅ 已完成 |
| v1.1 | 增强搜索：语义搜索（向量检索） + 相关性排序优化 | 🔄 规划中 |
| v1.2 | 协作能力：知识库导入导出 + 多人共享 | 📋 计划中 |
| v2.0 | 生态扩展：插件系统 + Web UI + API 服务 | 🔮 远期愿景 |

---

## 📦 打包与部署指南

### 🏗️ 本地构建

```bash
# 安装构建工具
pip install build

# 构建 sdist 和 wheel
python -m build

# 构建产物位于 dist/ 目录
ls dist/
# mindflow_cli-1.0.0.tar.gz
# mindflow_cli-1.0.0-py3-none-any.whl
```

### 📤 发布到 PyPI

```bash
# 安装 Twine
pip install twine

# 检查包内容
twine check dist/*

# 上传到 PyPI（TestPyPI 先测试）
twine upload --repository testpypi dist/*
twine upload dist/*
```

### 🐳 Docker 部署

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
ENTRYPOINT ["mindflow"]
```

```bash
# 构建镜像
docker build -t mindflow-cli .

# 运行容器
docker run -it -v ~/.mindflow:/root/.mindflow mindflow-cli init
```

### 🧪 运行测试

```bash
# 运行全部测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=mindflow_cli --cov-report=html

# 运行特定模块测试
pytest tests/test_search_engine.py -v
```

---

## 🤝 贡献指南

我们欢迎并感谢每一位贡献者！无论你是修复 Bug、添加新功能，还是改进文档，每一份贡献都让 MindFlow-CLI 变得更好。

### 🔄 贡献流程

1. **🍴 Fork** 本仓库到你的 GitHub 账号
2. **🌿 Clone** 你 Fork 的仓库到本地
3. **🔧 创建分支** — `git checkout -b feature/your-feature-name`
4. **✏️ 编写代码** — 遵循现有代码风格，添加必要的测试
5. **🧪 运行测试** — 确保 `pytest` 全部通过
6. **📝 提交 PR** — 附上清晰的变更说明

### 📋 代码规范

- 遵循 **PEP 8** 代码风格
- 为新功能编写**对应的单元测试**
- 保持**向后兼容**，避免破坏性变更
- 提交信息遵循 **Conventional Commits** 规范

### 🐛 问题反馈

如果在使用过程中遇到任何问题，欢迎通过 [GitHub Issues](https://github.com/gitstq/MindFlow-CLI/issues) 提交反馈，请尽量附上复现步骤和环境信息。

---

## 📄 开源协议

本项目基于 [MIT License](https://github.com/gitstq/MindFlow-CLI/blob/main/LICENSE) 开源，你可以自由使用、修改和分发。

```
MIT License

Copyright (c) 2024 gitstq

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a> · Powered by Python
</p>

---
---

<!-- language-anchor:zh-TW -->

# 🧠 MindFlow-CLI

<p align="center">
  <b>輕量級 AI 知識工作流自動化引擎</b><br>
  <i>純 Python 實現 · 零外部依賴 · 開箱即用</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/python-3.8%2B-yellow" alt="Python">
  <img src="https://img.shields.io/badge/tests-151%20passed-success" alt="Tests">
  <img src="https://img.shields.io/badge/code-8300%2B%20lines-orange" alt="Code">
</p>

---

## 🎉 專案介紹

**MindFlow-CLI** 是一款面向知識工作者與開發者的**命令列知識管理工具**，它將知識片段管理、智慧搜尋、AI 工作流編排與模板化輸出融為一體，幫助你在終端中高效完成從「資訊採集」到「知識沉澱」的全鏈路閉環。

無論你是需要整理研究筆記的研究員、梳理會議紀要的專案經理，還是希望用 AI 加速日常工作的開發者，MindFlow-CLI 都能成為你得心應手的效率利器。

### 🌟 為什麼選擇 MindFlow-CLI？

- **🪶 輕量極致** — 純 Python 實現，零外部依賴，`pip install` 即可使用
- **🧩 模組化設計** — 知識管理、搜尋引擎、工作流引擎、模板系統各司其職，可獨立運作也可無縫協作
- **🤖 AI 原生** — 內建多 LLM 整合，支援 OpenAI / Anthropic / Ollama，讓 AI 真正融入你的知識工作流
- **📊 終端美學** — 精心打磨的 TUI 互動式儀表板，讓命令列也能賞心悅目
- **🧪 品質可靠** — 8300+ 行程式碼，151 個測試全部通過，覆蓋核心業務邏輯

---

## ✨ 核心特性

### 📝 知識片段管理
完整的 CRUD 操作，支援**標籤分類**與**全文搜尋**，讓你的每一條知識都有跡可循。

```bash
# 新增一條知識片段
mindflow add --title "Python 裝飾器" --content "裝飾器是Python中用於修改函式行為的語法糖..." --tags python,語法

# 查看所有知識片段
mindflow list

# 搜尋知識
mindflow search "裝飾器"
```

### 🔗 DAG 工作流引擎
基於**有向無環圖（DAG）**的工作流編排引擎，支援條件分支與平行執行，讓複雜的知識處理流程變得清晰可控。

```bash
# 執行工作流
mindflow workflow run research_pipeline

# 查看可用工作流
mindflow workflow list
```

### 🤖 多 LLM 整合
統一的介面層對接 **OpenAI / Anthropic / Ollama**，一處設定、多處呼叫，靈活切換模型供應商。

```bash
# 設定 LLM
mindflow config set llm.provider openai
mindflow config set llm.model gpt-4
```

### 🔍 TF-IDF + BM25 混合搜尋引擎
自研混合搜尋引擎，融合 **TF-IDF** 與 **BM25** 演算法，原生支援中英文雙語檢索，精準定位你需要的知識。

```bash
# 全文搜尋
mindflow search "機器學習入門"

# 按標籤篩選
mindflow search --tags AI,教學
```

### 📋 模板系統
內建 **6 個精心設計的預設模板**，覆蓋常見知識工作場景：

| 模板名稱 | 適用場景 |
|---------|---------|
| 📚 研究整理 | 學術論文、技術調研的結構化整理 |
| 📝 會議紀要 | 會議要點提煉與行動項追蹤 |
| 📖 學習筆記 | 課程筆記、讀書筆記的系統化記錄 |
| 📂 專案文件 | 專案架構、API 文件的規範化輸出 |
| 🔎 程式碼審查 | Code Review 要點與改進建議 |
| 📊 週報生成 | 一週工作總結與下週計畫 |

```bash
# 查看可用模板
mindflow template list

# 套用模板
mindflow template apply 研究整理 --title "大模型技術調研"
```

### 📊 TUI 互動式儀表板
基於 **curses** 的終端互動介面，即時展示知識庫統計、標籤分佈、近期活動等關鍵資訊。

```bash
# 啟動儀表板
mindflow tui
```

### 📤 多格式匯出
支援匯出為 **JSON / Markdown / HTML** 三種格式，方便分享與二次加工。

```bash
# 匯出為 Markdown
mindflow export markdown --output notes.md

# 匯出為 HTML
mindflow export html --output report.html

# 匯出為 JSON
mindflow export json --output data.json
```

### 💾 SQLite 儲存引擎
內建 **SQLite** 持久化方案，零設定開箱即用，資料安全可靠，支援百萬級知識片段的高效儲存與檢索。

---

## 🚀 快速開始

### 📋 環境需求

- **Python** >= 3.8
- **作業系統**：Windows / macOS / Linux（跨平台支援）

### 🔧 安裝

```bash
# 從 PyPI 安裝（推薦）
pip install mindflow-cli

# 或從原始碼安裝
git clone https://github.com/gitstq/MindFlow-CLI.git
cd MindFlow-CLI
pip install -e .
```

### ⚡ 三步上手

```bash
# 1️⃣ 初始化知識庫
mindflow init

# 2️⃣ 新增第一條知識
mindflow add --title "我的第一條知識" --content "MindFlow-CLI 讓知識管理變得簡單高效！" --tags 入門

# 3️⃣ 搜尋與查看
mindflow search "知識"
mindflow list
```

### 🎯 快速體驗工作流

```bash
# 建立一個研究工作流
mindflow workflow create research_flow

# 執行工作流
mindflow workflow run research_flow

# 查看執行結果
mindflow stats
```

---

## 📖 詳細使用指南

### 📝 知識片段操作

```bash
# ➕ 新增知識片段
mindflow add --title "標題" --content "內容" --tags "標籤1,標籤2"

# 📋 列出所有知識片段
mindflow list
mindflow list --tags python          # 按標籤篩選
mindflow list --limit 10            # 限制顯示數量

# 🔍 搜尋知識片段
mindflow search "關鍵字"
mindflow search "關鍵字" --tags AI  # 組合搜尋

# 👁️ 查看知識片段詳情
mindflow show <id>

# 🗑️ 刪除知識片段
mindflow delete <id>

# 🏷️ 標籤管理
mindflow tags                       # 查看所有標籤
mindflow tags --sort count          # 按使用次數排序
```

### 🔗 工作流管理

```bash
# 📋 查看工作流列表
mindflow workflow list

# ➕ 建立工作流
mindflow workflow create <name>

# 🚀 執行工作流
mindflow workflow run <name>

# 📊 查看工作流執行歷史
mindflow workflow run <name> --history
```

### 📋 模板使用

```bash
# 📋 查看可用模板
mindflow template list

# 🎯 套用模板產生內容
mindflow template apply <模板名> --title "標題"
```

### 📤 匯出功能

```bash
# 匯出為不同格式
mindflow export json --output data.json
mindflow export markdown --output notes.md
mindflow export html --output report.html

# 按標籤篩選匯出
mindflow export markdown --tags "AI,研究" --output ai_research.md
```

### ⚙️ 設定管理

```bash
# 查看目前設定
mindflow config

# 設定配置項
mindflow config set llm.provider openai
mindflow config set llm.model gpt-4
mindflow config set llm.api_key sk-xxx

# 查看統計資訊
mindflow stats
```

---

## 💡 設計思路與迭代規劃

### 🏗️ 架構設計理念

MindFlow-CLI 遵循以下核心設計原則：

1. **單一職責** — 每個模組只做一件事，做到極致（儲存引擎只管存取，搜尋引擎只管檢索）
2. **介面抽象** — 透過統一的抽象層對接不同 LLM 供應商，切換模型無需改動業務程式碼
3. **漸進增強** — 核心功能零依賴可用，AI 能力按需開啟
4. **資料本地化** — 所有資料儲存在本機 SQLite，隱私安全有保障

### 📁 專案結構

```
MindFlow-CLI/
├── mindflow_cli/          # 核心原始碼
│   ├── cli.py             # 命令列入口
│   ├── storage.py         # SQLite 儲存引擎
│   ├── search_engine.py   # TF-IDF + BM25 搜尋引擎
│   ├── workflow_engine.py # DAG 工作流引擎
│   ├── llm_client.py      # 多 LLM 統一客戶端
│   ├── template_manager.py# 模板管理器
│   ├── exporter.py        # 多格式匯出器
│   ├── tui.py             # TUI 互動式儀表板
│   ├── models.py          # 資料模型定義
│   ├── config.py          # 設定管理
│   └── utils.py           # 工具函式
├── tests/                 # 測試套件（151 個測試）
├── pyproject.toml         # 專案配置
├── setup.py               # 安裝配置
└── LICENSE                # MIT 授權條款
```

### 🗺️ 迭代規劃

| 階段 | 內容 | 狀態 |
|------|------|------|
| v1.0 | 核心功能：知識管理 + 搜尋 + 工作流 + 模板 + 匯出 | ✅ 已完成 |
| v1.1 | 增強搜尋：語義搜尋（向量檢索） + 相關性排序最佳化 | 🔄 規劃中 |
| v1.2 | 協作能力：知識庫匯入匯出 + 多人共享 | 📋 計畫中 |
| v2.0 | 生態擴展：外掛系統 + Web UI + API 服務 | 🔮 遠期願景 |

---

## 📦 打包與部署指南

### 🏗️ 本地建構

```bash
# 安裝建構工具
pip install build

# 建構 sdist 和 wheel
python -m build

# 建構產物位於 dist/ 目錄
ls dist/
# mindflow_cli-1.0.0.tar.gz
# mindflow_cli-1.0.0-py3-none-any.whl
```

### 📤 發佈到 PyPI

```bash
# 安裝 Twine
pip install twine

# 檢查套件內容
twine check dist/*

# 上傳到 PyPI（TestPyPI 先測試）
twine upload --repository testpypi dist/*
twine upload dist/*
```

### 🐳 Docker 部署

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
ENTRYPOINT ["mindflow"]
```

```bash
# 建構映像
docker build -t mindflow-cli .

# 執行容器
docker run -it -v ~/.mindflow:/root/.mindflow mindflow-cli init
```

### 🧪 執行測試

```bash
# 執行全部測試
pytest

# 執行測試並產生覆蓋率報告
pytest --cov=mindflow_cli --cov-report=html

# 執行特定模組測試
pytest tests/test_search_engine.py -v
```

---

## 🤝 貢獻指南

我們歡迎並感謝每一位貢獻者！無論你是修復 Bug、新增功能，還是改善文件，每一份貢獻都讓 MindFlow-CLI 變得更好。

### 🔄 貢獻流程

1. **🍴 Fork** 本倉庫到你的 GitHub 帳號
2. **🌿 Clone** 你 Fork 的倉庫到本機
3. **🔧 建立分支** — `git checkout -b feature/your-feature-name`
4. **✏️ 撰寫程式碼** — 遵循現有程式碼風格，新增必要的測試
5. **🧪 執行測試** — 確保 `pytest` 全部通過
6. **📝 提交 PR** — 附上清晰的變更說明

### 📋 程式碼規範

- 遵循 **PEP 8** 程式碼風格
- 為新功能撰寫**對應的單元測試**
- 保持**向後相容**，避免破壞性變更
- 提交訊息遵循 **Conventional Commits** 規範

### 🐛 問題回饋

如果在使用過程中遇到任何問題，歡迎透過 [GitHub Issues](https://github.com/gitstq/MindFlow-CLI/issues) 提交回饋，請盡量附上重現步驟與環境資訊。

---

## 📄 開源協議

本專案基於 [MIT License](https://github.com/gitstq/MindFlow-CLI/blob/main/LICENSE) 開源，你可以自由使用、修改與分發。

```
MIT License

Copyright (c) 2024 gitstq

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a> · Powered by Python
</p>

---
---

<!-- language-anchor:en -->

# 🧠 MindFlow-CLI

<p align="center">
  <b>Lightweight AI Knowledge Workflow Automation Engine</b><br>
  <i>Pure Python · Zero External Dependencies · Ready to Use</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/python-3.8%2B-yellow" alt="Python">
  <img src="https://img.shields.io/badge/tests-151%20passed-success" alt="Tests">
  <img src="https://img.shields.io/badge/code-8300%2B%20lines-orange" alt="Code">
</p>

---

## 🎉 Introduction

**MindFlow-CLI** is a **command-line knowledge management tool** built for knowledge workers and developers. It brings together knowledge snippet management, intelligent search, AI workflow orchestration, and template-based output into a single cohesive experience, helping you close the loop from "information gathering" to "knowledge consolidation" — all within your terminal.

Whether you're a researcher organizing notes, a project manager distilling meeting minutes, or a developer looking to supercharge your workflow with AI, MindFlow-CLI is the productivity companion you've been looking for.

### 🌟 Why MindFlow-CLI?

- **🪶 Ultra Lightweight** — Pure Python with zero external dependencies; just `pip install` and go
- **🧩 Modular Design** — Knowledge management, search engine, workflow engine, and template system work independently or seamlessly together
- **🤖 AI-Native** — Built-in multi-LLM integration with OpenAI / Anthropic / Ollama support, making AI a natural part of your knowledge workflow
- **📊 Terminal Aesthetics** — A polished TUI interactive dashboard that makes the command line a joy to use
- **🧪 Battle-Tested** — 8300+ lines of code, 151 tests all passing, covering core business logic

---

## ✨ Core Features

### 📝 Knowledge Snippet Management
Full CRUD operations with **tag-based categorization** and **full-text search**, ensuring every piece of knowledge is always within reach.

```bash
# Add a knowledge snippet
mindflow add --title "Python Decorators" --content "Decorators are syntactic sugar in Python for modifying function behavior..." --tags python,syntax

# List all snippets
mindflow list

# Search knowledge
mindflow search "decorator"
```

### 🔗 DAG Workflow Engine
A workflow orchestration engine built on **Directed Acyclic Graphs (DAG)**, supporting conditional branching and parallel execution to keep complex knowledge processing pipelines clear and controllable.

```bash
# Run a workflow
mindflow workflow run research_pipeline

# List available workflows
mindflow workflow list
```

### 🤖 Multi-LLM Integration
A unified interface layer connecting to **OpenAI / Anthropic / Ollama** — configure once, call everywhere, and switch model providers with ease.

```bash
# Configure LLM
mindflow config set llm.provider openai
mindflow config set llm.model gpt-4
```

### 🔍 TF-IDF + BM25 Hybrid Search Engine
A custom hybrid search engine combining **TF-IDF** and **BM25** algorithms with native bilingual support for both Chinese and English, delivering precise knowledge retrieval.

```bash
# Full-text search
mindflow search "machine learning basics"

# Filter by tags
mindflow search --tags AI,tutorial
```

### 📋 Template System
**6 carefully crafted preset templates** covering common knowledge work scenarios:

| Template | Use Case |
|----------|----------|
| 📚 Research Summary | Structured organization of academic papers and technical research |
| 📝 Meeting Minutes | Key takeaways extraction and action item tracking |
| 📖 Study Notes | Systematic recording of course and reading notes |
| 📂 Project Docs | Standardized output for project architecture and API documentation |
| 🔎 Code Review | Code review highlights and improvement suggestions |
| 📊 Weekly Report | Weekly work summary and next week's plan |

```bash
# List available templates
mindflow template list

# Apply a template
mindflow template apply "Research Summary" --title "LLM Technology Survey"
```

### 📊 TUI Interactive Dashboard
A terminal-based interactive interface powered by **curses**, displaying real-time statistics, tag distribution, recent activity, and other key insights.

```bash
# Launch the dashboard
mindflow tui
```

### 📤 Multi-Format Export
Export to **JSON / Markdown / HTML** formats for easy sharing and further processing.

```bash
# Export as Markdown
mindflow export markdown --output notes.md

# Export as HTML
mindflow export html --output report.html

# Export as JSON
mindflow export json --output data.json
```

### 💾 SQLite Storage Engine
Built-in **SQLite** persistence — zero configuration, ready out of the box. Reliable data storage supporting efficient retrieval of millions of knowledge snippets.

---

## 🚀 Quick Start

### 📋 Prerequisites

- **Python** >= 3.8
- **OS**: Windows / macOS / Linux (cross-platform support)

### 🔧 Installation

```bash
# Install from PyPI (recommended)
pip install mindflow-cli

# Or install from source
git clone https://github.com/gitstq/MindFlow-CLI.git
cd MindFlow-CLI
pip install -e .
```

### ⚡ Three Steps to Get Started

```bash
# 1️⃣ Initialize your knowledge base
mindflow init

# 2️⃣ Add your first knowledge snippet
mindflow add --title "My First Snippet" --content "MindFlow-CLI makes knowledge management simple and efficient!" --tags getting-started

# 3️⃣ Search and explore
mindflow search "knowledge"
mindflow list
```

### 🎯 Try a Workflow

```bash
# Create a research workflow
mindflow workflow create research_flow

# Run the workflow
mindflow workflow run research_flow

# View results
mindflow stats
```

---

## 📖 Detailed Usage Guide

### 📝 Knowledge Snippet Operations

```bash
# ➕ Add a snippet
mindflow add --title "Title" --content "Content" --tags "tag1,tag2"

# 📋 List all snippets
mindflow list
mindflow list --tags python          # Filter by tag
mindflow list --limit 10            # Limit results

# 🔍 Search snippets
mindflow search "keyword"
mindflow search "keyword" --tags AI  # Combined search

# 👁️ View snippet details
mindflow show <id>

# 🗑️ Delete a snippet
mindflow delete <id>

# 🏷️ Tag management
mindflow tags                       # List all tags
mindflow tags --sort count          # Sort by usage count
```

### 🔗 Workflow Management

```bash
# 📋 List workflows
mindflow workflow list

# ➕ Create a workflow
mindflow workflow create <name>

# 🚀 Run a workflow
mindflow workflow run <name>

# 📊 View execution history
mindflow workflow run <name> --history
```

### 📋 Template Usage

```bash
# 📋 List available templates
mindflow template list

# 🎯 Apply a template
mindflow template apply <template-name> --title "Title"
```

### 📤 Export

```bash
# Export in different formats
mindflow export json --output data.json
mindflow export markdown --output notes.md
mindflow export html --output report.html

# Filter by tags when exporting
mindflow export markdown --tags "AI,research" --output ai_research.md
```

### ⚙️ Configuration

```bash
# View current config
mindflow config

# Set config values
mindflow config set llm.provider openai
mindflow config set llm.model gpt-4
mindflow config set llm.api_key sk-xxx

# View statistics
mindflow stats
```

---

## 💡 Design Philosophy & Roadmap

### 🏗️ Architecture Principles

MindFlow-CLI is built on these core design principles:

1. **Single Responsibility** — Each module does one thing and does it well (storage engine handles persistence, search engine handles retrieval)
2. **Interface Abstraction** — A unified abstraction layer connects to different LLM providers; switching models requires zero changes to business logic
3. **Progressive Enhancement** — Core features work with zero dependencies; AI capabilities are enabled on demand
4. **Local-First Data** — All data is stored in a local SQLite database, ensuring privacy and security

### 📁 Project Structure

```
MindFlow-CLI/
├── mindflow_cli/          # Core source code
│   ├── cli.py             # CLI entry point
│   ├── storage.py         # SQLite storage engine
│   ├── search_engine.py   # TF-IDF + BM25 search engine
│   ├── workflow_engine.py # DAG workflow engine
│   ├── llm_client.py      # Multi-LLM unified client
│   ├── template_manager.py# Template manager
│   ├── exporter.py        # Multi-format exporter
│   ├── tui.py             # TUI interactive dashboard
│   ├── models.py          # Data model definitions
│   ├── config.py          # Configuration management
│   └── utils.py           # Utility functions
├── tests/                 # Test suite (151 tests)
├── pyproject.toml         # Project configuration
├── setup.py               # Installation configuration
└── LICENSE                # MIT License
```

### 🗺️ Roadmap

| Phase | Content | Status |
|-------|---------|--------|
| v1.0 | Core: Knowledge management + Search + Workflow + Templates + Export | ✅ Done |
| v1.1 | Enhanced Search: Semantic search (vector retrieval) + Ranking optimization | 🔄 Planned |
| v1.2 | Collaboration: Knowledge base import/export + Multi-user sharing | 📋 Upcoming |
| v2.0 | Ecosystem: Plugin system + Web UI + API service | 🔮 Long-term Vision |

---

## 📦 Packaging & Deployment Guide

### 🏗️ Local Build

```bash
# Install build tools
pip install build

# Build sdist and wheel
python -m build

# Build artifacts are in the dist/ directory
ls dist/
# mindflow_cli-1.0.0.tar.gz
# mindflow_cli-1.0.0-py3-none-any.whl
```

### 📤 Publishing to PyPI

```bash
# Install Twine
pip install twine

# Check package contents
twine check dist/*

# Upload to PyPI (test with TestPyPI first)
twine upload --repository testpypi dist/*
twine upload dist/*
```

### 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
ENTRYPOINT ["mindflow"]
```

```bash
# Build the image
docker build -t mindflow-cli .

# Run the container
docker run -it -v ~/.mindflow:/root/.mindflow mindflow-cli init
```

### 🧪 Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=mindflow_cli --cov-report=html

# Run specific module tests
pytest tests/test_search_engine.py -v
```

---

## 🤝 Contributing

We welcome and appreciate every contributor! Whether you're fixing bugs, adding features, or improving documentation, every contribution makes MindFlow-CLI better.

### 🔄 Contribution Workflow

1. **🍴 Fork** this repository to your GitHub account
2. **🌿 Clone** your fork locally
3. **🔧 Create a branch** — `git checkout -b feature/your-feature-name`
4. **✏️ Write code** — Follow the existing code style and add appropriate tests
5. **🧪 Run tests** — Make sure `pytest` passes completely
6. **📝 Submit a PR** — Include a clear description of the changes

### 📋 Code Standards

- Follow **PEP 8** code style
- Write **unit tests** for new features
- Maintain **backward compatibility** — avoid breaking changes
- Use **Conventional Commits** for commit messages

### 🐛 Bug Reports

If you encounter any issues, please submit feedback via [GitHub Issues](https://github.com/gitstq/MindFlow-CLI/issues). Please include reproduction steps and environment details whenever possible.

---

## 📄 License

This project is open-sourced under the [MIT License](https://github.com/gitstq/MindFlow-CLI/blob/main/LICENSE). You are free to use, modify, and distribute it.

```
MIT License

Copyright (c) 2024 gitstq

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a> · Powered by Python
</p>
