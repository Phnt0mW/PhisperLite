# PhisperLite

中文 | [English](./README.en.md)

PhisperLite 是一个本地运行的桌面工具，用来把音频或视频处理成双语字幕。

它的思路很直接：

- 用 `ffmpeg` 提取音轨
- 用本地 `whisper.cpp` 做语音识别
- 用本地 GGUF 大模型做字幕翻译
- 最终输出双语 `.srt` 字幕文件

整个流程都在本机完成，不依赖在线字幕服务。

## 适合谁

- 想给视频做双语字幕的人
- 想离线处理音频转字幕的人
- 想自己准备模型和工具、不想把大模型打进安装包的人

## 当前支持

- macOS
- Windows

说明：
- 代码已经做了 Windows/macOS 双平台适配
- macOS 仍然是当前更成熟的首发平台
- Windows 需要你自己准备对应的 `ffmpeg.exe` 和 `whisper-cli.exe`

## 它会产出什么

处理完成后，程序会在源文件目录下生成：

- `xxx.translated.srt`

如果源文件目录不可写，程序会自动回退到项目的 `output/` 目录。

## 使用前你需要准备什么

PhisperLite 本体不内置以下大文件，你需要自行下载并放到 `resources/` 目录：

- `ffmpeg` 或 `ffmpeg.exe`
- `whisper-cli` 或 `whisper-cli.exe`
- `ggml-large-v3-turbo.bin`
- 至少一个翻译模型

支持的翻译模型：

- `Hunyuan-MT-7B-q4_k_m.gguf`
- `Qwen2.5-7B-Instruct-GGUF` 分片文件

## 下载地址

你可以从下面这些官方或模型页面获取资源：

- `whisper.cpp` Releases: https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.3/whisper-bin-x64.zip
- `FFmpeg` Windows builds page: https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z
- `Hunyuan-MT-7B-GGUF`: https://huggingface.co/Mungert/Hunyuan-MT-7B-GGUF/tree/main
- `Qwen2.5-7B-Instruct-GGUF`: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF

补充说明：

- macOS 下通常使用没有扩展名的二进制文件，比如 `ffmpeg`、`whisper-cli`
- Windows 下通常使用 `.exe`，比如 `ffmpeg.exe`、`whisper-cli.exe`
- `ggml-large-v3-turbo.bin` 一般来自 `whisper.cpp` 相关模型下载流程
- Qwen 模型通常是多分片文件，需要把完整分片都放进去

## resources 目录应该怎么放

最小目录结构示例：

```text
resources/
  ffmpeg
  ffmpeg.exe
  whisper-cli
  whisper-cli.exe
  ggml-large-v3-turbo.bin
  Hunyuan-MT-7B-q4_k_m.gguf
```

如果你想用 Qwen，通常会是这样：

```text
resources/
  ffmpeg
  ffmpeg.exe
  whisper-cli
  whisper-cli.exe
  ggml-large-v3-turbo.bin
  qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
  qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf
```

说明：

- 不需要同时放 mac 和 Windows 两套二进制，按你自己的系统准备即可
- 程序会自动按平台优先选择合适的可执行文件
- 图标资源也已经按平台做了选择逻辑

## 怎么开始用

1. 启动程序
2. 先选择你的 `resources/` 目录
3. 点击“检查资源”
4. 选择一个音频或视频文件
5. 选择翻译模型
6. 点击“开始处理”
7. 等待输出字幕

如果资源不完整，界面会直接提示缺少哪些文件。

## 开发环境启动

```bash
python -m venv venv
```

macOS/Linux:

```bash
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## 打包

先安装打包工具：

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

```bash
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

因为模型和工具体积都比较大，把它们和应用打在一起会让仓库、安装包和更新流程变得很重。

### 2. Windows 和 macOS 能共用同一个 resources 吗？

模型文件可以共用，但 `ffmpeg` 和 `whisper-cli` 这种可执行文件要按平台分别准备。

### 3. 输出文件在哪里？

默认优先输出到源文件所在目录；如果那里不可写，就会回退到 `output/`。

### 4. Windows 上翻译速度或兼容性为什么和 mac 不一样？

当前代码里对 `llama_cpp` 做了更稳妥的双平台默认配置：

- macOS 默认 `n_gpu_layers=-1`
- Windows 默认 `n_gpu_layers=0`

你也可以通过环境变量 `PHISPER_N_GPU_LAYERS` 自己覆盖。

## 项目结构

```text
main.py
core/
service/
ui/
utils/
resources/
```

## 相关说明

双平台适配的额外说明见：

- [WINDOWS_MACOS_NOTES.md](WINDOWS_MACOS_NOTES.md)

## License

MIT
