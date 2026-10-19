# PhisperLite v0.1.0

PhisperLite 是一款本地离线字幕工具，可将音频或视频转换为双语 `.srt` 字幕，完整流程均在本机完成。

## v0.1.0 发布版本

### macOS（Apple Silicon）

- 资源名：`PhisperLite-macos-arm64-v0.1.0.zip`
- 适用系统：macOS（M 系列芯片）
- 发布形式：桌面应用（`.app`）

### Windows（x64）

- 资源名：`PhisperLite-windows-x64.zip`
- 适用系统：Windows 10/11 64 位
- 发布形式：解压即用（`PhisperLite.exe` + `_internal`）

## 首次使用准备

本 Release 不内置大模型和外部工具，请自行准备 `resources/` 目录。启动程序后，先在界面中选择资源目录，再开始处理任务。

至少需要：

```text
resources/
  ffmpeg(.exe)
  whisper-cli(.exe)
  ggml-large-v3-turbo.bin
  一个翻译模型（Hunyuan 或 Qwen）
```

使用 Qwen 时，需要放入完整分片：

```text
resources/
  qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
  qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf
```

## 快速开始

1. 下载并解压对应平台的版本。
2. 启动 PhisperLite。
3. 选择 `resources/` 目录并点击“检查资源”。
4. 选择音频或视频文件。
5. 选择翻译模型并点击“开始处理”。
6. 完成后，在源文件目录（或 `output/`）中查看字幕结果。

## v0.1.0 功能

- 支持 macOS 和 Windows 双平台运行
- 支持本地 `whisper.cpp` 语音识别
- 支持本地 GGUF 翻译模型生成双语字幕
- 输出标准 `.srt` 字幕文件

## 注意事项

- Windows 用户请保留解压后的完整目录结构，不要单独移动 `PhisperLite.exe`。
- 如果出现“资源不完整”提示，请优先检查 `ffmpeg`、`whisper-cli`、`ggml-large-v3-turbo.bin` 和翻译模型是否齐全。
- 建议同时下载 `SHA256SUMS.txt`，校验文件完整性。
