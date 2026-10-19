# PhisperLite

中文 | [English](./README.en.md)

PhisperLite 是一款完全本地运行的桌面字幕工具，可将音频或视频制作成双语字幕。所有处理都在本机完成：免费、没有输出数量限制，也不会上传任何数据。

处理流程：

- 使用 `ffmpeg` 提取音轨
- 使用本地 `whisper.cpp` 进行语音识别
- 使用本地 GGUF 大模型翻译字幕
- 输出双语 `.srt` 字幕文件

## 适合谁

- 需要为视频制作双语字幕的内容创作者
- 希望在离线环境中完成音频转字幕的用户
- 不希望受在线服务额度或隐私限制的用户

## 支持的平台

- macOS
- Windows

说明：

- 代码已适配 Windows 和 macOS
- macOS 是当前更成熟的平台，90% 以上的测试在 macOS 上完成；Windows 版本保证可用
- 两个平台的运行时资源不通用，需要按平台分别准备

## 输出内容

处理完成后，程序会在源文件所在目录生成：

- `xxx.translated.srt`

如果源文件目录不可写，程序会自动回退到项目的 `output/` 目录。

## 使用前准备

PhisperLite 不内置以下大文件，请自行下载并放入 `resources/` 目录：

- `ffmpeg` 或 `ffmpeg.exe`：音频处理
- `whisper-cli` 或 `whisper-cli.exe`：语音识别
- `ggml-large-v3-turbo.bin`：Whisper 模型
- 至少一个翻译模型（推荐 Hunyuan）

支持的翻译模型：

- `Hunyuan-MT-7B-q4_k_m.gguf`（首选）
- `Qwen2.5-7B-Instruct-GGUF` 分片文件

## 下载地址

可以从以下官方页面获取所需资源：

- [whisper.cpp Releases](https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.3/whisper-bin-x64.zip)
- [FFmpeg Windows builds](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z)
- [Hunyuan-MT-7B-GGUF](https://huggingface.co/Mungert/Hunyuan-MT-7B-GGUF/tree/main)
- [Qwen2.5-7B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)

> 注意：以上二进制链接默认指向 Windows 版本。请确认下载的资源和你的平台匹配，并能在本机正常运行。

## `resources/` 目录结构

最小示例：

```text
resources/
  ffmpeg(.exe)
  whisper-cli(.exe)
  ggml-large-v3-turbo.bin
  Hunyuan-MT-7B-q4_k_m.gguf
```

使用 Qwen 时：

```text
resources/
  ffmpeg(.exe)
  whisper-cli(.exe)
  ggml-large-v3-turbo.bin
  qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
  qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf
```

说明：

- macOS 的可执行文件通常没有扩展名，例如 `ffmpeg`、`whisper-cli`；Windows 使用 `.exe`
- 不需要同时准备两个平台的二进制文件，按当前系统准备即可
- 程序会自动选择当前平台的可执行文件和图标
- 使用 Qwen 时，需要放入完整的分片文件

## 快速开始

1. 启动程序
2. 选择 `resources/` 目录
3. 点击“检查资源”
4. 选择音频或视频文件
5. 选择翻译模型
6. 点击“开始处理”
7. 在源文件目录或 `output/` 中查看生成的 `xxx.translated.srt`

如果资源不完整，界面会提示缺少哪些文件。

## 自行改造

如果你想二次开发，可以按以下方式启动和打包。

### 开发环境

```bash
python -m venv venv
```

macOS / Linux：

```bash
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Windows PowerShell：

```powershell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### 打包

先安装 PyInstaller：

```bash
pip install pyinstaller
```

macOS 示例：

```bash
pyinstaller \
  --noconfirm \
  --windowed \
  --name PhisperLite \
  --icon resources/icon.icns \
  --exclude-module torch \
  --exclude-module tensorflow \
  --exclude-module transformers \
  --collect-all llama_cpp \
  main.py
```

Windows 示例：

```bat
pyinstaller ^
  --noconfirm ^
  --windowed ^
  --name PhisperLite ^
  --icon resources/icon.ico ^
  --exclude-module torch ^
  --exclude-module tensorflow ^
  --exclude-module transformers ^
  --collect-all llama_cpp ^
  main.py
```

## 常见问题

### 1. 为什么程序本体不直接附带模型？

模型和运行时工具体积较大，打包进应用会让仓库、安装包和更新流程变得很重。

### 2. Windows 和 macOS 能共用同一个 `resources/` 目录吗？

模型文件可以共用，但 `ffmpeg` 和 `whisper-cli` 这类可执行文件需要按平台分别准备。

### 3. 输出文件在哪里？

默认优先输出到源文件所在目录；如果那里不可写，程序会自动回退到 `output/`。

### 4. Windows 上的翻译速度或兼容性为什么和 macOS 不同？

当前对 `llama_cpp` 采用按平台区分的默认配置：

- macOS 默认使用 `n_gpu_layers=-1`
- Windows 默认使用 `n_gpu_layers=0`

你也可以通过环境变量 `PHISPER_N_GPU_LAYERS` 覆盖这个设置。

## 项目结构

```text
main.py          程序入口
core/            音频提取、语音识别与字幕翻译
service/         工作流编排
ui/              界面与后台任务
utils/           配置与日志
resources/       本地运行时资源
```

## 相关说明

本项目在开发中大量使用了 AI 工具，代码仍有优化空间。

欢迎任意形式的改造和二次开发，也可以自行发布或提交 Pull Request。

Windows / macOS 的额外说明见 [WINDOWS_MACOS_NOTES.md](WINDOWS_MACOS_NOTES.md)。

## License

MIT
