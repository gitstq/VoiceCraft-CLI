<p align="center">
  <h1 align="center">🎙️ VoiceCraft-CLI</h1>
  <p align="center">
    <strong>Lightweight Terminal Voice Synthesis & Audio Processing Engine</strong>
  </p>
  <p align="center">
    轻量级终端语音合成与音频处理引擎
  </p>
  <p align="center">
    <a href="#-简体中文">简体中文</a> ·
    <a href="#-繁體中文">繁體中文</a> ·
    <a href="#-english">English</a>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
    <img src="https://img.shields.io/badge/Dependencies-Zero-success.svg" alt="Zero Dependencies">
    <img src="https://img.shields.io/badge/Tests-106%20Passed-brightgreen.svg" alt="Tests">
  </p>
</p>

---

<a id="-简体中文"></a>

## 🎉 项目介绍

**VoiceCraft-CLI** 是一款轻量级终端语音合成与音频处理引擎，纯 Python 实现，**零外部依赖**。它能够自动发现并适配系统中可用的 TTS 引擎，提供完整的语音合成、音频后处理、SSML 标记解析和批量合成能力。

### 💡 灵感来源

受 GitHub Trending 热门项目 `supertonic`（极速本地 TTS 引擎）启发，VoiceCraft-CLI 专注于为终端用户提供一个**开箱即用、零配置、跨平台**的语音合成解决方案。不同于需要复杂依赖的 TTS 工具，VoiceCraft-CLI 利用 Python 标准库实现了完整的音频处理管线。

### 🔥 自研差异化亮点

- **零依赖架构**：纯 Python 标准库实现，无需安装任何第三方包
- **多引擎智能适配**：自动发现 pyttsx3、espeak、系统 TTS，按优先级选择最优引擎
- **纯 Python 音频处理**：音量调节、归一化、淡入淡出、重采样、静音裁剪，全部纯 Python 实现
- **完整 SSML 支持**：解析 `<speak>`、`<break>`、`<prosody>`、`<emphasis>`、`<say-as>` 等标签
- **批量合成队列**：支持从文件/目录批量读取文本，带进度回调
- **TUI 交互仪表盘**：ANSI 彩色终端 UI，实时显示合成进度与引擎状态

---

## ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 🤖 **多引擎自动发现** | 智能检测 pyttsx3 → espeak → 系统 TTS，自动选择可用引擎 |
| 🎵 **纯 Python 音频处理** | 音量调节、归一化、淡入淡出、重采样、静音裁剪、WAV 拼接 |
| 📝 **SSML 标记解析** | 完整支持 SSML 1.1 标准标签，精细控制语音合成 |
| 📦 **批量合成队列** | 从文件/目录批量读取文本，异步队列处理，进度回调 |
| 🖥️ **TUI 交互仪表盘** | ANSI 彩色终端界面，实时显示引擎状态、合成进度、音频信息 |
| ⚙️ **灵活配置系统** | INI 配置文件 + 环境变量覆盖（`VOICECRAFT_*`） |
| 🔌 **插件化引擎架构** | 基于抽象基类的引擎接口，轻松扩展新引擎 |
| 📊 **音频信息查询** | 查看 WAV 文件详细信息（采样率、声道、时长等） |
| 🌍 **跨平台兼容** | 支持 Windows、macOS、Linux 三大平台 |
| 🧪 **完善测试覆盖** | 106 个单元测试，覆盖所有核心模块 |

---

## 🚀 快速开始

### 📋 环境要求

- **Python 3.8+**（无其他依赖）
- 可选：pyttsx3 / espeak / 系统 TTS（用于实际语音合成）

### 📥 安装

```bash
# 克隆仓库
git clone https://github.com/gitstq/VoiceCraft-CLI.git
cd VoiceCraft-CLI

# 安装（开发模式）
pip install -e .
```

### 🎮 基本使用

```bash
# 查看帮助
python -m voicecraft_cli --help

# 查看版本
python -m voicecraft_cli --version

# 列出可用引擎
python -m voicecraft_cli --list-engines

# 列出可用语音
python -m voicecraft_cli --list-voices

# 文本转语音（播放）
python -m voicecraft_cli --text "你好，欢迎使用 VoiceCraft-CLI"

# 文本转语音（保存为文件）
python -m voicecraft_cli --text "Hello World" --output hello.wav

# 从文件读取文本并合成
python -m voicecraft_cli --file input.txt --output output.wav

# 调节语速和音量
python -m voicecraft_cli --text "快速朗读测试" --rate 200 --volume 0.8

# 使用 SSML 标记
python -m voicecraft_cli --ssml --text '<speak><prosody rate="slow">这是一段慢速语音</prosody><break time="500ms"/><prosody rate="fast">这是一段快速语音</prosody></speak>' --output ssml_test.wav

# 批量合成
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/

# 查看 WAV 文件信息
python -m voicecraft_cli --info audio.wav

# 启用 TUI 仪表盘
python -m voicecraft_cli --tui --text "仪表盘模式演示"
```

---

## 📖 详细使用指南

### 🔧 引擎管理

VoiceCraft-CLI 支持多种 TTS 引擎，按以下优先级自动选择：

1. **pyttsx3**（需安装：`pip install pyttsx3`）
2. **espeak / espeak-ng**（需安装：`apt install espeak`）
3. **系统 TTS**（macOS `say`、Windows SAPI、Linux `spd-say`）

```bash
# 指定引擎
python -m voicecraft_cli --engine pyttsx3 --text "使用 pyttsx3 引擎"
python -m voicecraft_cli --engine espeak --text "使用 espeak 引擎"
python -m voicecraft_cli --engine system --text "使用系统引擎"

# 查看引擎详细信息
python -m voicecraft_cli --list-engines --verbose
```

### 🎵 音频处理

```bash
# 调节音量（0.0-1.0）
python -m voicecraft_cli --text "音量测试" --volume 0.5

# 调节语速（50-300 WPM）
python -m voicecraft_cli --text "语速测试" --rate 150

# 调节音调（-10.0 到 10.0 半音）
python -m voicecraft_cli --text "音调测试" --pitch 2.0

# 指定输出格式
python -m voicecraft_cli --text "格式测试" --output test.wav --format wav
```

### 📝 SSML 使用

SSML（Speech Synthesis Markup Language）允许精细控制语音合成：

```bash
python -m voicecraft_cli --ssml --text '
<speak>
  <p>这是一段段落。</p>
  <break time="1s"/>
  <prosody rate="slow" pitch="+2st">
    这段话会被慢速朗读，音调升高。
  </prosody>
  <emphasis level="strong">这段话会被强调。</emphasis>
  <say-as interpret-as="digits">2024</say-as>
</speak>
' --output ssml_output.wav
```

### 📦 批量合成

```bash
# 从目录批量合成（支持 .txt、.ssml 文件）
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/

# 指定输出格式和引擎
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/ --engine espeak --format wav

# 递归扫描子目录
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/ --recursive
```

### ⚙️ 配置文件

在项目根目录或 `~/.voicecraft/` 下创建 `config.ini`：

```ini
[engine]
default = pyttsx3
fallback = espeak,system

[audio]
default_format = wav
sample_rate = 22050
channels = 1

[synthesis]
default_rate = 180
default_volume = 1.0
default_pitch = 0.0

[batch]
max_workers = 4
recursive = false
```

环境变量覆盖：

```bash
export VOICECRAFT_ENGINE=espeak
export VOICECRAFT_RATE=200
export VOICECRAFT_VOLUME=0.8
python -m voicecraft_cli --text "环境变量配置测试"
```

---

## 💡 设计思路与迭代规划

### 🎯 设计理念

- **零依赖优先**：所有核心功能使用 Python 标准库实现，降低用户使用门槛
- **渐进增强**：无 TTS 引擎时优雅降级，有引擎时自动利用最佳能力
- **插件化架构**：基于抽象基类的引擎接口，方便社区贡献新引擎适配
- **终端原生**：所有交互在终端完成，TUI 仪表盘提供直观的可视化反馈

### 🛠️ 技术选型

| 模块 | 技术方案 | 原因 |
|------|---------|------|
| CLI 解析 | argparse | Python 标准库，零依赖 |
| 音频处理 | wave + struct + array | 纯标准库，跨平台 |
| SSML 解析 | xml.etree.ElementTree | 标准库 XML 解析 |
| 终端 UI | ANSI 转义码 | 无需额外依赖 |
| 配置管理 | configparser | 标准库 INI 解析 |
| 日志系统 | logging | 标准库日志模块 |

### 📅 后续迭代计划

- [ ] 添加更多 TTS 引擎适配（Azure Cognitive Services、Google Cloud TTS）
- [ ] 支持 MP3/AAC/OGG 格式输出（通过 subprocess 调用 ffmpeg）
- [ ] 添加语音克隆功能（基于预训练模型）
- [ ] 实现实时流式合成
- [ ] 添加 Web API 服务模式
- [ ] 支持更多 SSML 1.1 扩展标签

---

## 📦 打包与部署

### 🔨 本地安装

```bash
# 从源码安装
git clone https://github.com/gitstq/VoiceCraft-CLI.git
cd VoiceCraft-CLI
pip install -e .

# 或直接使用
python -m voicecraft_cli --help
```

### 🐍 PyPI 安装（计划中）

```bash
pip install voicecraft-cli
```

### 🐳 Docker 部署（计划中）

```bash
docker run -it --rm voicecraft-cli --text "Docker 部署测试"
```

### 🖥️ 系统兼容性

| 平台 | 支持状态 | 推荐引擎 |
|------|---------|---------|
| 🪟 Windows | ✅ 完全支持 | pyttsx3 / SAPI |
| 🍎 macOS | ✅ 完全支持 | pyttsx3 / say |
| 🐧 Linux | ✅ 完全支持 | espeak / pyttsx3 |

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！请遵循以下规范：

### 📋 提交 PR 流程

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'feat: add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

### 📝 提交规范

遵循 Angular 提交规范：

- `feat:` 新增功能
- `fix:` 修复问题
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具变更

### 🐛 Issue 反馈

提交 Issue 时请包含：
- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息（Python 版本、操作系统、TTS 引擎）

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

```
MIT License

Copyright (c) 2026 VoiceCraft-CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>

---

<a id="-繁體中文"></a>

## 🎉 專案介紹

**VoiceCraft-CLI** 是一款輕量級終端語音合成與音訊處理引擎，純 Python 實現，**零外部依賴**。它能夠自動發現並適配系統中可用的 TTS 引擎，提供完整的語音合成、音訊後處理、SSML 標記解析和批量合成能力。

### 💡 靈感來源

受 GitHub Trending 熱門專案 `supertonic`（極速本地 TTS 引擎）啟發，VoiceCraft-CLI 專注於為終端用戶提供一個**開箱即用、零配置、跨平台**的語音合成解決方案。不同於需要複雜依賴的 TTS 工具，VoiceCraft-CLI 利用 Python 標準庫實現了完整的音訊處理管線。

### 🔥 自研差異化亮點

- **零依賴架構**：純 Python 標準庫實現，無需安裝任何第三方套件
- **多引擎智慧適配**：自動發現 pyttsx3、espeak、系統 TTS，按優先級選擇最優引擎
- **純 Python 音訊處理**：音量調節、歸一化、淡入淡出、重取樣、靜音裁剪，全部純 Python 實現
- **完整 SSML 支援**：解析 `<speak>`、`<break>`、`<prosody>`、`<emphasis>`、`<say-as>` 等標籤
- **批量合成佇列**：支援從檔案/目錄批量讀取文本，帶進度回呼
- **TUI 互動儀表板**：ANSI 彩色終端 UI，即時顯示合成進度與引擎狀態

---

## ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 🤖 **多引擎自動發現** | 智慧檢測 pyttsx3 → espeak → 系統 TTS，自動選擇可用引擎 |
| 🎵 **純 Python 音訊處理** | 音量調節、歸一化、淡入淡出、重取樣、靜音裁剪、WAV 拼接 |
| 📝 **SSML 標記解析** | 完整支援 SSML 1.1 標準標籤，精細控制語音合成 |
| 📦 **批量合成佇列** | 從檔案/目錄批量讀取文本，非同步佇列處理，進度回呼 |
| 🖥️ **TUI 互動儀表板** | ANSI 彩色終端介面，即時顯示引擎狀態、合成進度、音訊資訊 |
| ⚙️ **靈活配置系統** | INI 配置檔案 + 環境變數覆蓋（`VOICECRAFT_*`） |
| 🔌 **外掛化引擎架構** | 基於抽象基類的引擎介面，輕鬆擴展新引擎 |
| 📊 **音訊資訊查詢** | 查看 WAV 檔案詳細資訊（取樣率、聲道、時長等） |
| 🌍 **跨平台相容** | 支援 Windows、macOS、Linux 三大平台 |
| 🧪 **完善測試覆蓋** | 106 個單元測試，覆蓋所有核心模組 |

---

## 🚀 快速開始

### 📋 環境要求

- **Python 3.8+**（無其他依賴）
- 可選：pyttsx3 / espeak / 系統 TTS（用於實際語音合成）

### 📥 安裝

```bash
# 克隆倉庫
git clone https://github.com/gitstq/VoiceCraft-CLI.git
cd VoiceCraft-CLI

# 安裝（開發模式）
pip install -e .
```

### 🎮 基本使用

```bash
# 查看幫助
python -m voicecraft_cli --help

# 查看版本
python -m voicecraft_cli --version

# 列出可用引擎
python -m voicecraft_cli --list-engines

# 列出可用語音
python -m voicecraft_cli --list-voices

# 文本轉語音（播放）
python -m voicecraft_cli --text "你好，歡迎使用 VoiceCraft-CLI"

# 文本轉語音（儲存為檔案）
python -m voicecraft_cli --text "Hello World" --output hello.wav

# 從檔案讀取文本並合成
python -m voicecraft_cli --file input.txt --output output.wav

# 調節語速和音量
python -m voicecraft_cli --text "快速朗讀測試" --rate 200 --volume 0.8

# 使用 SSML 標記
python -m voicecraft_cli --ssml --text '<speak><prosody rate="slow">這是一段慢速語音</prosody><break time="500ms"/><prosody rate="fast">這是一段快速語音</prosody></speak>' --output ssml_test.wav

# 批量合成
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/

# 查看 WAV 檔案資訊
python -m voicecraft_cli --info audio.wav

# 啟用 TUI 儀表板
python -m voicecraft_cli --tui --text "儀表板模式演示"
```

---

## 📖 詳細使用指南

### 🔧 引擎管理

VoiceCraft-CLI 支援多種 TTS 引擎，按以下優先級自動選擇：

1. **pyttsx3**（需安裝：`pip install pyttsx3`）
2. **espeak / espeak-ng**（需安裝：`apt install espeak`）
3. **系統 TTS**（macOS `say`、Windows SAPI、Linux `spd-say`）

```bash
# 指定引擎
python -m voicecraft_cli --engine pyttsx3 --text "使用 pyttsx3 引擎"
python -m voicecraft_cli --engine espeak --text "使用 espeak 引擎"
python -m voicecraft_cli --engine system --text "使用系統引擎"

# 查看引擎詳細資訊
python -m voicecraft_cli --list-engines --verbose
```

### 🎵 音訊處理

```bash
# 調節音量（0.0-1.0）
python -m voicecraft_cli --text "音量測試" --volume 0.5

# 調節語速（50-300 WPM）
python -m voicecraft_cli --text "語速測試" --rate 150

# 調節音調（-10.0 到 10.0 半音）
python -m voicecraft_cli --text "音調測試" --pitch 2.0

# 指定輸出格式
python -m voicecraft_cli --text "格式測試" --output test.wav --format wav
```

### 📝 SSML 使用

SSML（Speech Synthesis Markup Language）允許精細控制語音合成：

```bash
python -m voicecraft_cli --ssml --text '
<speak>
  <p>這是一段段落。</p>
  <break time="1s"/>
  <prosody rate="slow" pitch="+2st">
    這段話會被慢速朗讀，音調升高。
  </prosody>
  <emphasis level="strong">這段話會被強調。</emphasis>
  <say-as interpret-as="digits">2024</say-as>
</speak>
' --output ssml_output.wav
```

### 📦 批量合成

```bash
# 從目錄批量合成（支援 .txt、.ssml 檔案）
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/

# 指定輸出格式和引擎
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/ --engine espeak --format wav

# 遞迴掃描子目錄
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/ --recursive
```

### ⚙️ 配置檔案

在專案根目錄或 `~/.voicecraft/` 下建立 `config.ini`：

```ini
[engine]
default = pyttsx3
fallback = espeak,system

[audio]
default_format = wav
sample_rate = 22050
channels = 1

[synthesis]
default_rate = 180
default_volume = 1.0
default_pitch = 0.0

[batch]
max_workers = 4
recursive = false
```

環境變數覆蓋：

```bash
export VOICECRAFT_ENGINE=espeak
export VOICECRAFT_RATE=200
export VOICECRAFT_VOLUME=0.8
python -m voicecraft_cli --text "環境變數配置測試"
```

---

## 💡 設計思路與迭代規劃

### 🎯 設計理念

- **零依賴優先**：所有核心功能使用 Python 標準庫實現，降低用戶使用門檻
- **漸進增強**：無 TTS 引擎時優雅降級，有引擎時自動利用最佳能力
- **外掛化架構**：基於抽象基類的引擎介面，方便社群貢獻新引擎適配
- **終端原生**：所有互動在終端完成，TUI 儀表板提供直觀的視覺化回饋

### 🛠️ 技術選型

| 模組 | 技術方案 | 原因 |
|------|---------|------|
| CLI 解析 | argparse | Python 標準庫，零依賴 |
| 音訊處理 | wave + struct + array | 純標準庫，跨平台 |
| SSML 解析 | xml.etree.ElementTree | 標準庫 XML 解析 |
| 終端 UI | ANSI 跳脫碼 | 無需額外依賴 |
| 配置管理 | configparser | 標準庫 INI 解析 |
| 日誌系統 | logging | 標準庫日誌模組 |

### 📅 後續迭代計畫

- [ ] 新增更多 TTS 引擎適配（Azure Cognitive Services、Google Cloud TTS）
- [ ] 支援 MP3/AAC/OGG 格式輸出（透過 subprocess 呼叫 ffmpeg）
- [ ] 新增語音克隆功能（基於預訓練模型）
- [ ] 實現即時串流合成
- [ ] 新增 Web API 服務模式
- [ ] 支援更多 SSML 1.1 擴展標籤

---

## 📦 打包與部署

### 🔨 本地安裝

```bash
# 從原始碼安裝
git clone https://github.com/gitstq/VoiceCraft-CLI.git
cd VoiceCraft-CLI
pip install -e .

# 或直接使用
python -m voicecraft_cli --help
```

### 🐍 PyPI 安裝（計畫中）

```bash
pip install voicecraft-cli
```

### 🐳 Docker 部署（計畫中）

```bash
docker run -it --rm voicecraft-cli --text "Docker 部署測試"
```

### 🖥️ 系統相容性

| 平台 | 支援狀態 | 推薦引擎 |
|------|---------|---------|
| 🪟 Windows | ✅ 完全支援 | pyttsx3 / SAPI |
| 🍎 macOS | ✅ 完全支援 | pyttsx3 / say |
| 🐧 Linux | ✅ 完全支援 | espeak / pyttsx3 |

---

## 🤝 貢獻指南

我們歡迎所有形式的貢獻！請遵循以下規範：

### 📋 提交 PR 流程

1. Fork 本倉庫
2. 建立特性分支：`git checkout -b feature/amazing-feature`
3. 提交變更：`git commit -m 'feat: add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

### 📝 提交規範

遵循 Angular 提交規範：

- `feat:` 新增功能
- `fix:` 修復問題
- `docs:` 文件更新
- `refactor:` 程式碼重構
- `test:` 測試相關
- `chore:` 建構/工具變更

### 🐛 Issue 回饋

提交 Issue 時請包含：
- 問題描述
- 重現步驟
- 期望行為
- 實際行為
- 環境資訊（Python 版本、作業系統、TTS 引擎）

---

## 📄 開源協議

本專案基於 [MIT License](LICENSE) 開源。

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>

---

<a id="-english"></a>

## 🎉 Introduction

**VoiceCraft-CLI** is a lightweight terminal voice synthesis and audio processing engine built entirely with Python and **zero external dependencies**. It automatically discovers and adapts to available TTS engines on your system, providing complete speech synthesis, audio post-processing, SSML markup parsing, and batch synthesis capabilities.

### 💡 Inspiration

Inspired by the GitHub Trending project `supertonic` (a blazing-fast on-device TTS engine), VoiceCraft-CLI focuses on delivering an **out-of-the-box, zero-config, cross-platform** voice synthesis solution for terminal users. Unlike TTS tools that require complex dependencies, VoiceCraft-CLI leverages the Python standard library to implement a complete audio processing pipeline.

### 🔥 Differentiated Highlights

- **Zero-Dependency Architecture**: Built entirely with Python standard library — no third-party packages needed
- **Multi-Engine Smart Adapter**: Auto-discovers pyttsx3, espeak, and system TTS, selecting the best available engine
- **Pure Python Audio Processing**: Volume adjustment, normalization, fade in/out, resampling, silence trimming — all in pure Python
- **Full SSML Support**: Parses `<speak>`, `<break>`, `<prosody>`, `<emphasis>`, `<say-as>` and more
- **Batch Synthesis Queue**: Reads text from files/directories in bulk with progress callbacks
- **TUI Interactive Dashboard**: ANSI-colored terminal UI with real-time synthesis progress and engine status

---

## ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🤖 **Multi-Engine Auto-Discovery** | Intelligently detects pyttsx3 → espeak → system TTS, auto-selects available engine |
| 🎵 **Pure Python Audio Processing** | Volume adjustment, normalization, fade in/out, resampling, silence trimming, WAV concatenation |
| 📝 **SSML Markup Parsing** | Full SSML 1.1 standard tag support for fine-grained synthesis control |
| 📦 **Batch Synthesis Queue** | Bulk text reading from files/directories with async queue processing and progress callbacks |
| 🖥️ **TUI Interactive Dashboard** | ANSI-colored terminal interface with real-time engine status, synthesis progress, and audio info |
| ⚙️ **Flexible Configuration** | INI config files + environment variable overrides (`VOICECRAFT_*`) |
| 🔌 **Plugin Engine Architecture** | Abstract base class engine interface for easy extension |
| 📊 **Audio Info Query** | View detailed WAV file information (sample rate, channels, duration, etc.) |
| 🌍 **Cross-Platform Compatible** | Full support for Windows, macOS, and Linux |
| 🧪 **Comprehensive Test Coverage** | 106 unit tests covering all core modules |

---

## 🚀 Quick Start

### 📋 Requirements

- **Python 3.8+** (no other dependencies required)
- Optional: pyttsx3 / espeak / system TTS (for actual speech synthesis)

### 📥 Installation

```bash
# Clone the repository
git clone https://github.com/gitstq/VoiceCraft-CLI.git
cd VoiceCraft-CLI

# Install (development mode)
pip install -e .
```

### 🎮 Basic Usage

```bash
# Show help
python -m voicecraft_cli --help

# Show version
python -m voicecraft_cli --version

# List available engines
python -m voicecraft_cli --list-engines

# List available voices
python -m voicecraft_cli --list-voices

# Text-to-speech (play)
python -m voicecraft_cli --text "Hello, welcome to VoiceCraft-CLI"

# Text-to-speech (save to file)
python -m voicecraft_cli --text "Hello World" --output hello.wav

# Read from file and synthesize
python -m voicecraft_cli --file input.txt --output output.wav

# Adjust rate and volume
python -m voicecraft_cli --text "Speed test" --rate 200 --volume 0.8

# Use SSML markup
python -m voicecraft_cli --ssml --text '<speak><prosody rate="slow">This is slow speech</prosody><break time="500ms"/><prosody rate="fast">This is fast speech</prosody></speak>' --output ssml_test.wav

# Batch synthesis
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/

# View WAV file info
python -m voicecraft_cli --info audio.wav

# Enable TUI dashboard
python -m voicecraft_cli --tui --text "Dashboard mode demo"
```

---

## 📖 Detailed Usage Guide

### 🔧 Engine Management

VoiceCraft-CLI supports multiple TTS engines with automatic priority-based selection:

1. **pyttsx3** (install: `pip install pyttsx3`)
2. **espeak / espeak-ng** (install: `apt install espeak`)
3. **System TTS** (macOS `say`, Windows SAPI, Linux `spd-say`)

```bash
# Specify engine
python -m voicecraft_cli --engine pyttsx3 --text "Using pyttsx3 engine"
python -m voicecraft_cli --engine espeak --text "Using espeak engine"
python -m voicecraft_cli --engine system --text "Using system engine"

# View detailed engine info
python -m voicecraft_cli --list-engines --verbose
```

### 🎵 Audio Processing

```bash
# Adjust volume (0.0-1.0)
python -m voicecraft_cli --text "Volume test" --volume 0.5

# Adjust rate (50-300 WPM)
python -m voicecraft_cli --text "Rate test" --rate 150

# Adjust pitch (-10.0 to 10.0 semitones)
python -m voicecraft_cli --text "Pitch test" --pitch 2.0

# Specify output format
python -m voicecraft_cli --text "Format test" --output test.wav --format wav
```

### 📝 SSML Usage

SSML (Speech Synthesis Markup Language) allows fine-grained control over speech synthesis:

```bash
python -m voicecraft_cli --ssml --text '
<speak>
  <p>This is a paragraph.</p>
  <break time="1s"/>
  <prosody rate="slow" pitch="+2st">
    This sentence will be read slowly with a higher pitch.
  </prosody>
  <emphasis level="strong">This sentence will be emphasized.</emphasis>
  <say-as interpret-as="digits">2024</say-as>
</speak>
' --output ssml_output.wav
```

### 📦 Batch Synthesis

```bash
# Batch synthesis from directory (supports .txt, .ssml files)
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/

# Specify output format and engine
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/ --engine espeak --format wav

# Recursive directory scanning
python -m voicecraft_cli --batch --input-dir ./texts/ --output-dir ./audio/ --recursive
```

### ⚙️ Configuration

Create a `config.ini` in the project root or `~/.voicecraft/`:

```ini
[engine]
default = pyttsx3
fallback = espeak,system

[audio]
default_format = wav
sample_rate = 22050
channels = 1

[synthesis]
default_rate = 180
default_volume = 1.0
default_pitch = 0.0

[batch]
max_workers = 4
recursive = false
```

Environment variable overrides:

```bash
export VOICECRAFT_ENGINE=espeak
export VOICECRAFT_RATE=200
export VOICECRAFT_VOLUME=0.8
python -m voicecraft_cli --text "Environment variable config test"
```

---

## 💡 Design Philosophy & Roadmap

### 🎯 Design Principles

- **Zero-Dependency First**: All core features implemented with Python standard library to minimize user friction
- **Progressive Enhancement**: Graceful degradation without TTS engines, automatic optimization when engines are available
- **Plugin Architecture**: Abstract base class engine interface for easy community contributions
- **Terminal-Native**: All interactions in the terminal with TUI dashboard for intuitive visual feedback

### 🛠️ Technology Choices

| Module | Technology | Rationale |
|--------|-----------|-----------|
| CLI Parsing | argparse | Python standard library, zero dependencies |
| Audio Processing | wave + struct + array | Pure standard library, cross-platform |
| SSML Parsing | xml.etree.ElementTree | Standard library XML parser |
| Terminal UI | ANSI escape codes | No additional dependencies |
| Configuration | configparser | Standard library INI parser |
| Logging | logging | Standard library logging module |

### 📅 Roadmap

- [ ] Add more TTS engine adapters (Azure Cognitive Services, Google Cloud TTS)
- [ ] Support MP3/AAC/OGG output formats (via ffmpeg subprocess)
- [ ] Add voice cloning capabilities (based on pre-trained models)
- [ ] Implement real-time streaming synthesis
- [ ] Add Web API server mode
- [ ] Support additional SSML 1.1 extension tags

---

## 📦 Packaging & Deployment

### 🔨 Local Installation

```bash
# Install from source
git clone https://github.com/gitstq/VoiceCraft-CLI.git
cd VoiceCraft-CLI
pip install -e .

# Or use directly
python -m voicecraft_cli --help
```

### 🐍 PyPI Installation (Planned)

```bash
pip install voicecraft-cli
```

### 🐳 Docker Deployment (Planned)

```bash
docker run -it --rm voicecraft-cli --text "Docker deployment test"
```

### 🖥️ System Compatibility

| Platform | Status | Recommended Engine |
|----------|--------|-------------------|
| 🪟 Windows | ✅ Full Support | pyttsx3 / SAPI |
| 🍎 macOS | ✅ Full Support | pyttsx3 / say |
| 🐧 Linux | ✅ Full Support | espeak / pyttsx3 |

---

## 🤝 Contributing

We welcome all forms of contributions! Please follow these guidelines:

### 📋 PR Submission Process

1. Fork this repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'feat: add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Submit a Pull Request

### 📝 Commit Convention

Follow the Angular commit convention:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation update
- `refactor:` Code refactoring
- `test:` Test-related changes
- `chore:` Build/tooling changes

### 🐛 Issue Reporting

When submitting an issue, please include:
- Problem description
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment info (Python version, OS, TTS engine)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

```
MIT License

Copyright (c) 2026 VoiceCraft-CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>
