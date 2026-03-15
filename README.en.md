# Phisperlite

***

PhisperLite is a lightweight desktop tool for local workflows, used to process audio and video into bilingual subtitles.

Its goal is straightforward:

- Extract audio and video tracks
- Perform speech recognition using the local `whisper-cli`
- Generate bilingual subtitles using a local GGUF translation model
- Distributed as a lightweight `.app` package, without bundling large models directly into the installer

## Features

- Runs locally, no dependency on online subtitle services
- Lightweight macOS application package
- Allows manual selection of the `resources` folder after launch
- Supports two local translation models: `Hunyuan` and `Qwen`
- Processing includes status, progress and log output

## Platform

- macOS
- Apple Silicon (`arm64`) is prioritized for support at present
- Python 3.11 is used for local development and packaging

## Quick Start

1. Download or build `PhisperLite.app`
2. Prepare the local `resources/` folder
3. Launch the application
4. Click **Select Resource Directory**
5. Click **Check Resources**
6. Select an audio or video file and start processing

## Required Resources

The application itself does **not** include large model resources. Please prepare a local `resources/` folder before first use.

The repository also does not commit `ffmpeg`, `whisper-cli`, or model files, keeping the source code repository lightweight.

The minimal directory structure is as follows:

```text
resources/
  ffmpeg
  whisper-cli
  ggml-large-v3-turbo.bin
  Hunyuan-MT-7B-q4_k_m.gguf
```

If you want to use Qwen as the translation model, please prepare the full shards:

```text
resources/
  ffmpeg
  whisper-cli
  ggml-large-v3-turbo.bin
  qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
  qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf
```

The filenames of resources used in the current project are consistent with the local verification logic, for details please refer to [utils/config.py](utils/config.py).

## Local Development

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Packaging

First, install the packaging tools:

```bash
source venv/bin/activate
pip install pyinstaller
```

Build the lightweight macOS package:

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

After building, you will get:

- `dist/PhisperLite.app`

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
- This project currently prioritizes local usability and lightweight distribution.
- If the resource directory is incomplete, the app will prompt the user to configure it instead of crashing directly.
- The icon, resource directory, and log directory in the current version have been adapted to the lightweight packaging workflow.

## License
This project is licensed under the [MIT License](LICENSE).