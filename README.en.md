# PhisperLite

[中文](./README.md) | English

PhisperLite is a fully local desktop subtitle tool that turns audio or video into bilingual subtitles. Everything runs on your machine: it is free, has no output limits, and never uploads your data.

The workflow:

- Extract audio with `ffmpeg`
- Run speech recognition with local `whisper.cpp`
- Translate subtitles with a local GGUF model
- Export a bilingual `.srt` subtitle file

## Who It Is For

- Content creators who need bilingual subtitles for their videos
- Users who want to transcribe audio offline
- Users who prefer not to deal with online service quotas or privacy concerns

## Supported Platforms

- macOS
- Windows

Notes:

- The codebase supports both Windows and macOS
- macOS is the more mature platform: over 90% of testing is done on macOS, while Windows builds are supported and usable
- Runtime assets differ by platform and must be prepared separately

## Output

After processing, the app generates:

- `xxx.translated.srt`

The app tries to write next to the source file first. If that directory is not writable, it falls back to the project's `output/` directory.

## Before You Start

PhisperLite does not bundle the following large files. Download them and place them in the `resources/` directory:

- `ffmpeg` or `ffmpeg.exe` for audio processing
- `whisper-cli` or `whisper-cli.exe` for speech recognition
- `ggml-large-v3-turbo.bin` for the Whisper model
- At least one translation model (Hunyuan is recommended)

Supported translation models:

- `Hunyuan-MT-7B-q4_k_m.gguf` (recommended)
- `Qwen2.5-7B-Instruct-GGUF` shard files

## Download Links

You can get the required assets from these official pages:

- [whisper.cpp releases](https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.3/whisper-bin-x64.zip)
- [FFmpeg Windows builds](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z)
- [Hunyuan-MT-7B-GGUF](https://huggingface.co/Mungert/Hunyuan-MT-7B-GGUF/tree/main)
- [Qwen2.5-7B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)

> Note: the binary links above point to Windows builds by default. Make sure the assets match your platform and run correctly on your machine.

## `resources/` Layout

Minimal example:

```text
resources/
  ffmpeg(.exe)
  whisper-cli(.exe)
  ggml-large-v3-turbo.bin
  Hunyuan-MT-7B-q4_k_m.gguf
```

With Qwen:

```text
resources/
  ffmpeg(.exe)
  whisper-cli(.exe)
  ggml-large-v3-turbo.bin
  qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
  qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf
```

Notes:

- macOS executables usually have no extension, such as `ffmpeg` and `whisper-cli`; Windows binaries use `.exe`
- You do not need binaries for both platforms; prepare the set for your current system
- The app automatically selects the executable and icon for the current platform
- When using Qwen, all shard files must be present

## Quick Start

1. Launch the app
2. Select your `resources/` directory
3. Click **Check Resources**
4. Select an audio or video file
5. Choose a translation model
6. Click **Start**
7. Find the generated `xxx.translated.srt` next to the source file or in `output/`

If required files are missing, the UI will list them.

## Customization

If you want to modify or extend the project, use the setup and packaging steps below.

### Development Environment

```bash
python -m venv venv
```

macOS / Linux:

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

### Packaging

Install PyInstaller first:

```bash
pip install pyinstaller
```

macOS example:

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

Windows example:

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

## FAQ

### 1. Why are models not bundled with the app?

Models and runtime tools are large. Bundling them would make the repository, installer, and update flow much heavier.

### 2. Can Windows and macOS share the same `resources/` directory?

Model files can be shared, but executables such as `ffmpeg` and `whisper-cli` must be prepared for each platform.

### 3. Where are output files written?

The app writes next to the source file first. If that location is not writable, it falls back to `output/`.

### 4. Why do translation speed and compatibility differ between Windows and macOS?

The app uses platform-specific `llama_cpp` defaults:

- macOS uses `n_gpu_layers=-1`
- Windows uses `n_gpu_layers=0`

You can override this with the `PHISPER_N_GPU_LAYERS` environment variable.

## Project Structure

```text
main.py          Application entry point
core/            Audio extraction, speech recognition, and translation
service/         Workflow orchestration
ui/              UI and background tasks
utils/           Configuration and logging
resources/       Local runtime assets
```

## Related Notes

This project makes heavy use of AI tools during development, so the code still has room for improvement.

Contributions, custom forks, and independent upgrades are welcome. You can publish your own version or open a pull request.

For additional Windows/macOS details, see [WINDOWS_MACOS_NOTES.md](WINDOWS_MACOS_NOTES.md).

## License

MIT
