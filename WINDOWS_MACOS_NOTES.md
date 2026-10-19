# Windows/macOS Compatibility Notes

PhisperLite keeps a macOS-first workflow while providing safer defaults on Windows.

本项目以 macOS 为主要平台，同时为 Windows 提供更稳妥的默认配置。

## Runtime

- Frozen builds choose a writable base directory for each platform.
- macOS prefers `~/Library/Application Support/PhisperLite`.
- Windows prefers `%LOCALAPPDATA%\PhisperLite` and falls back safely when it is unavailable.

打包后的程序会按平台自动选择可写的基础目录：

- macOS 优先使用 `~/Library/Application Support/PhisperLite`。
- Windows 优先使用 `%LOCALAPPDATA%\PhisperLite`，不可用时安全回退。

## Icons

- macOS prefers `icon.icns`.
- Windows prefers `favicon-2.ico` or `icon.ico`.
- Other platforms fall back to `icon.png`.

图标加载规则：

- macOS 优先使用 `icon.icns`。
- Windows 优先使用 `favicon-2.ico` 或 `icon.ico`。
- 其他平台回退到 `icon.png`。

## Translation Backend

- macOS uses `n_gpu_layers=-1` by default.
- Windows and other platforms use `n_gpu_layers=0` for better compatibility.
- Set `PHISPER_N_GPU_LAYERS` to override the default.

翻译后端的默认配置：

- macOS 默认使用 `n_gpu_layers=-1`。
- Windows 和其他平台默认使用 `n_gpu_layers=0`，以获得更好的兼容性。
- 可以通过环境变量 `PHISPER_N_GPU_LAYERS` 覆盖默认值。

## Resource Layout

Use binaries that match your platform:

请为不同平台准备对应的可执行文件：

```text
resources/
  ffmpeg / ffmpeg.exe
  whisper-cli / whisper-cli.exe
  ggml-large-v3-turbo.bin
  Hunyuan-MT-7B-q4_k_m.gguf
```

## Windows Packaging

Example PyInstaller command:

Windows 下的 PyInstaller 打包示例：

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
