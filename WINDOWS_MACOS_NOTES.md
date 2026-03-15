# Windows/macOS Compatibility Notes

This project now keeps the macOS-first behavior while adding safer Windows defaults.

本项目目前保留了 macOS 优先的运行方式，同时补充了对 Windows 更稳妥的默认配置。

## Runtime

- Frozen builds now choose a writable base directory per platform.
- macOS continues to prefer `~/Library/Application Support/PhisperLite`.
- Windows prefers `%LOCALAPPDATA%\\PhisperLite` and falls back safely if needed.

- 打包后的程序现在会按平台自动选择可写的基础目录。
- macOS 仍然优先使用 `~/Library/Application Support/PhisperLite`。
- Windows 优先使用 `%LOCALAPPDATA%\\PhisperLite`，如果不可用会安全回退到其他目录。

## Icons

- macOS prefers `icon.icns`.
- Windows prefers `favicon-2.ico` or `icon.ico`.
- Other platforms fall back to `icon.png`.

- macOS 优先使用 `icon.icns`。
- Windows 优先使用 `favicon-2.ico` 或 `icon.ico`。
- 其他平台会回退到 `icon.png`。

## Translation Backend

- macOS keeps `n_gpu_layers=-1` by default.
- Windows and other platforms default to `n_gpu_layers=0` for better compatibility.
- You can override this with `PHISPER_N_GPU_LAYERS`.

- macOS 默认保持 `n_gpu_layers=-1`。
- Windows 和其他平台默认使用 `n_gpu_layers=0`，兼容性更好。
- 你也可以通过环境变量 `PHISPER_N_GPU_LAYERS` 手动覆盖这个值。

## Resource Layout

Use matching binaries for each platform:

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

Windows 下的 PyInstaller 打包示例命令：

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
