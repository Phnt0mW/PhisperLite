# PhisperLite使用说明

中文 | [English](./README.en.md)

PhisperLite 是一个完全本地运行的桌面字幕工具，用来把音频或视频处理成双语字幕。
本项目完全基于目前的开源技术和产品。
它的思路很直接：

- 用 `ffmpeg` 提取音轨
- 用本地 `whisper.cpp` 做语音识别
- 用本地 GGUF 大模型做字幕翻译
- 最终输出双语 `.srt` 字幕文件

整个流程都在本机完成，完全免费，不会把任何数据上传到云端，也没有任何输出限制。

## 适合谁

- 视频搬运者
- 想离线处理音频转字幕的人
- 不希望收到在线服务限制

## 当前支持

- macOS
- Windows

说明：
- 代码已经做了 Windows/macOS 双平台适配
- macOS 仍然是当前更成熟的首发平台，90%以上的测试在mac上运行，Windows平台只保证可用
- 任何平台均需要自行下载资源文件，因为双平台资源版本不通用

## 它会产出什么

处理完成后，程序会在源文件目录下生成：

- `xxx.translated.srt`

如果源文件目录不可写，程序会自动回退到项目的 `output/` 目录。

## 使用前你需要准备什么

PhisperLite 本体不内置以下大文件，你需要自行下载并放到 `resources/` 目录：

- `ffmpeg` 或 `ffmpeg.exe`用于音频处理
- `whisper-cli` 或 `whisper-cli.exe`用于语音识别
- `ggml-large-v3-turbo.bin`
- 至少一个翻译模型（推荐用hunyuan模型）

支持的翻译模型：

- `Hunyuan-MT-7B-q4_k_m.gguf`（首选）
- `Qwen2.5-7B-Instruct-GGUF` 分片文件

## 下载地址

你可以从下面这些官方或模型页面获取资源：

注意：请一定选择适合自己平台的工具，请再三确保下载的版本可以在自己的电脑上运行
下方的链接直通Windows版本，请mac用户注意甄别
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

## 对于想要自行改造的用户

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

本项目大量使用ai工具，代码未必最优
本项目欢迎任意形式的改造和升级，你可以自行发布，也可以尝试pull request
双平台适配的额外说明见：

- [WINDOWS_MACOS_NOTES.md](WINDOWS_MACOS_NOTES.md)

## License

MIT
