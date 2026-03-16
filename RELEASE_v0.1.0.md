# PhisperLite v0.1.0

PhisperLite 是一款本地离线字幕工具。  
它可以把音频或视频处理成双语字幕（`.srt`），完整流程都在本机运行。

## v0.1.0 提供的版本

### macOS（Apple Silicon）

- 资源名：`PhisperLite-macos-arm64-v0.1.0.zip`
- 适用系统：macOS（M 系列芯片）
- 形态：桌面应用（`.app`）

### Windows（x64）

- 资源名：`PhisperLite-windows-x64.zip`
- 适用系统：Windows 10/11 64 位
- 形态：解压即用（`PhisperLite.exe` + `_internal`）

## 首次使用前需要准备

本 Release 不内置大模型与外部工具，请自行准备 `resources` 目录。  
程序启动后，先在界面里选择你的 `resources` 目录，再开始处理任务。

最低需要：

```text
resources/
  ffmpeg(.exe)
  whisper-cli(.exe)
  ggml-large-v3-turbo.bin
  一个翻译模型（Hunyuan 或 Qwen）
```

Qwen 需要完整分片（示例）：

```text
resources/
  qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
  qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf
```

## 快速开始

1. 下载并解压对应平台版本。
2. 启动 PhisperLite。
3. 选择 `resources` 目录并点击“检查资源”。
4. 选择音频/视频文件。
5. 选择翻译模型并开始处理。
6. 完成后在源文件目录（或 `output/`）查看字幕结果。

## v0.1.0 版本说明

- 支持 macOS 与 Windows 双平台运行。
- 支持本地 `whisper.cpp` 语音识别。
- 支持本地 GGUF 翻译模型生成双语字幕。
- 输出标准 `.srt` 字幕文件。

## 重要提示

- Windows 用户请保留解压后的完整目录结构，不要单独移动 `PhisperLite.exe`。
- 如果遇到“资源不完整”提示，优先检查 `ffmpeg`、`whisper-cli`、`ggml-large-v3-turbo.bin` 和翻译模型是否齐全。
- 建议同时下载 `SHA256SUMS.txt` 做文件完整性校验。
