# PhisperLite

PhisperLite 是一个面向本地工作流的轻量桌面工具，用来把音视频处理成双语字幕。

它的目标很直接：

- 提取音视频音轨
- 用本地 `whisper-cli` 做语音识别
- 用本地 GGUF 翻译模型生成双语字幕
- 以轻量 `.app` 的形式分发，而不是把超大模型直接打进安装包

## Features

- 本地运行，不依赖在线字幕服务
- 轻量版 macOS 应用包
- 启动后可手动选择 `resources` 文件夹
- 支持 `Hunyuan` 和 `Qwen` 两种本地翻译模型
- 处理过程带状态、进度和日志输出

## Platform

- macOS
- 当前优先支持 Apple Silicon (`arm64`)
- Python 3.11 用于本地开发与打包

## Quick Start

1. 下载或构建 `PhisperLite.app`
2. 准备本地 `resources/` 文件夹
3. 启动应用
4. 点击“选择资源目录”
5. 点击“检查资源”
6. 选择音频或视频文件并开始处理

## Required Resources

应用本体不内置大模型资源。首次使用前，请自行准备本地 `resources/` 文件夹。
仓库本身也不提交 `ffmpeg`、`whisper-cli` 和模型文件，保持源码仓库轻量。

最小目录结构如下：

```text
resources/
  ffmpeg
  whisper-cli
  ggml-large-v3-turbo.bin
  Hunyuan-MT-7B-q4_k_m.gguf
```

如果你想使用 Qwen 作为翻译模型，请准备完整分片：

```text
resources/
  ffmpeg
  whisper-cli
  ggml-large-v3-turbo.bin
  qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
  qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf
```

当前项目使用到的资源文件名与本地校验逻辑一致，具体可以参考 [utils/config.py](utils/config.py)。

## Local Development

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Packaging

先安装打包工具：

```bash
source venv/bin/activate
pip install pyinstaller
```

打轻量版 macOS 包：

```bash
env PYINSTALLER_CONFIG_DIR="$PWD/.pyinstaller" \
venv/bin/pyinstaller \
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

构建完成后会得到：

- `dist/PhisperLite.app`

如果要发布 Release，建议进一步压缩：

```bash
cd dist
ditto -c -k --sequesterRsrc --keepParent \
  PhisperLite.app \
  PhisperLite-macos-arm64-v0.1.0.zip
```

## GitHub Release Strategy

推荐的发布方式是：

1. GitHub 仓库只放源码、文档和轻量打包配置
2. GitHub Release 只放轻量版 `.app` 或 zip 包
3. 大模型、`ffmpeg`、`whisper-cli` 由用户本地准备
4. 在 Release 页面明确说明如何选择 `resources/` 文件夹

这样做的好处是：

- 仓库体积可控
- 安装包体积可控
- 模型可独立更新
- 不会被超大资源拖慢每次发版

## Suggested First Release

- Tag: `v0.1.0`
- Asset: `PhisperLite-macos-arm64-v0.1.0.zip`
- 文案草稿见 [RELEASE_v0.1.0.md](RELEASE_v0.1.0.md)

## Project Structure

```text
main.py
core/
service/
ui/
utils/
resources/
```

## Notes

- 本项目当前优先关注本地可用性和轻量分发
- 如果资源目录不完整，应用会提示用户配置，而不是直接崩溃
- 当前版本的图标、资源目录和日志目录都已经适配轻量包流程

## License

本项目使用 [MIT License](LICENSE)。
