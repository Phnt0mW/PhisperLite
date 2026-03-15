# PhisperLite v0.1.0

## Release Assets

- `PhisperLite-macos-arm64-v0.1.0.zip`

## Build Commands

从项目根目录执行：

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

构建完成后压缩 `.app`：

```bash
cd dist
ditto -c -k --sequesterRsrc --keepParent \
  PhisperLite.app \
  PhisperLite-macos-arm64-v0.1.0.zip
```

## Suggested Git Commands

```bash
git add .
git commit -m "feat: release v0.1.0"
git tag v0.1.0
git push origin main
git push origin v0.1.0
```

## Release Notes Draft

PhisperLite 是一个面向本地工作流的轻量桌面工具，可以完成音视频转写与双语字幕生成。

### Highlights

- 轻量版 macOS 应用包，不再内置超大模型资源
- 首次启动后可在界面中手动选择 `resources` 文件夹
- 支持本地 `whisper-cli` 转写
- 支持本地 GGUF 翻译模型生成双语字幕

### Notes

- 当前 Release 为 `macOS Apple Silicon (arm64)` 版本
- 应用本体不内置模型、`ffmpeg`、`whisper-cli`
- GitHub 仓库同样不提交这些大资源与平台二进制
- 首次启动后请点击“选择资源目录”，指向你本地准备好的 `resources/` 文件夹

### Required `resources/` Layout

```text
resources/
  ffmpeg
  whisper-cli
  ggml-large-v3-turbo.bin
  Hunyuan-MT-7B-q4_k_m.gguf
```

如果使用 Qwen，请改为：

```text
resources/
  ffmpeg
  whisper-cli
  ggml-large-v3-turbo.bin
  qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
  qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf
```

### Known Scope

- 当前主要面向 macOS 本地使用场景
- 首版发布优先保证流程可用和资源解耦
