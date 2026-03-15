# PhisperLite

PhisperLite is a local desktop tool for turning audio or video files into bilingual subtitles.

The workflow is simple:

- Extract audio with `ffmpeg`
- Run speech recognition with local `whisper.cpp`
- Translate subtitles with a local GGUF model
- Export a bilingual `.srt` subtitle file

Everything runs on your machine. No online subtitle service is required.

## Who It Is For

- People who want bilingual subtitles for videos
- People who want offline audio-to-subtitle workflows
- People who prefer to manage models and tools separately instead of bundling them into the app

## Current Platform Support

- macOS
- Windows

Notes:

- The codebase now includes Windows/macOS compatibility adjustments
- macOS is still the more mature primary platform
- On Windows, you need to prepare `ffmpeg.exe` and `whisper-cli.exe` yourself

## What It Outputs

After processing, the app will generate:

- `xxx.translated.srt`

The app will try to write output next to the source file first. If that directory is not writable, it falls back to `output/`.

## What You Need Before Running

PhisperLite does not bundle large runtime assets. You need to download and place these files into `resources/` yourself:

- `ffmpeg` or `ffmpeg.exe`
- `whisper-cli` or `whisper-cli.exe`
- `ggml-large-v3-turbo.bin`
- At least one translation model

Supported translation models:

- `Hunyuan-MT-7B-q4_k_m.gguf`
- `Qwen2.5-7B-Instruct-GGUF` shard files

## Download Links

You can get the required tools and models from these pages:

- `whisper.cpp` releases: https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.3/whisper-bin-x64.zip
- `FFmpeg` Windows builds page: https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z
- `Hunyuan-MT-7B-GGUF`: https://huggingface.co/Mungert/Hunyuan-MT-7B-GGUF/tree/main
- `Qwen2.5-7B-Instruct-GGUF`: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF

Extra notes:

- On macOS, binaries usually have no extension, such as `ffmpeg` and `whisper-cli`
- On Windows, binaries are usually `.exe`, such as `ffmpeg.exe` and `whisper-cli.exe`
- `ggml-large-v3-turbo.bin` usually comes from the `whisper.cpp` model download flow
- Qwen models are usually split into multiple shards, so make sure all required parts are present

## How To Arrange `resources/`

Minimal example:

```text
resources/
  ffmpeg
  ffmpeg.exe
  whisper-cli
  whisper-cli.exe
  ggml-large-v3-turbo.bin
  Hunyuan-MT-7B-q4_k_m.gguf
```

If you want to use Qwen, the directory will usually look like this:

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

Notes:

- You do not need both macOS and Windows binaries at the same time; only prepare the set for your current system
- The app will automatically choose the correct executable for the current platform
- Icon loading also follows platform-specific fallback rules now

## How To Use It

1. Launch the app
2. Select your `resources/` directory
3. Click `Check Resources`
4. Select an audio or video file
5. Choose a translation model
6. Click `Start`
7. Wait for subtitle export

If required files are missing, the UI will tell you what is missing.

## Development Setup

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

## Packaging

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

## FAQ

### Why are the models not bundled into the app?

Because the models and runtime tools are large. Keeping them outside the app makes the repository, installer, and update flow much lighter.

### Can Windows and macOS share the same `resources/` directory?

Model files can be shared, but platform-specific executables such as `ffmpeg` and `whisper-cli` need the correct binaries for each platform.

### Where are output files written?

The app tries to write next to the source file first. If that location is not writable, it falls back to `output/`.

### Why can translation speed or compatibility differ between Windows and macOS?

The current `llama_cpp` defaults are now platform-aware:

- macOS defaults to `n_gpu_layers=-1`
- Windows defaults to `n_gpu_layers=0`

You can override this with the `PHISPER_N_GPU_LAYERS` environment variable.

## Project Structure

```text
main.py
core/
service/
ui/
utils/
resources/
```

## Related Notes

For extra Windows/macOS compatibility details, see:

- [WINDOWS_MACOS_NOTES.md](WINDOWS_MACOS_NOTES.md)

## License

MIT
