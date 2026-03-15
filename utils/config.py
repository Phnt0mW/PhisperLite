import os
import platform
import sys
import tempfile
import json
from pathlib import Path

class PhisperConfig:
    TRANSLATOR_BACKENDS = {
        "hunyuan": "混元",
        "qwen": "千问",
    }

    def __init__(self):
        self._bundled_res_dir = None
        self._doc_search_dirs = []
        if getattr(sys, "frozen", False):
            executable_dir = Path(sys.executable).resolve().parent
            self._doc_search_dirs = [
                executable_dir,
                executable_dir.parent,
                executable_dir.parent / "Resources",
                Path(getattr(sys, "_MEIPASS", executable_dir)),
            ]
            bundle_resources = executable_dir.parent / "Resources" / "resources"
            meipass_resources = Path(getattr(sys, "_MEIPASS", executable_dir)) / "resources"

            if bundle_resources.exists():
                self._bundled_res_dir = bundle_resources
            elif meipass_resources.exists():
                self._bundled_res_dir = meipass_resources
            else:
                self._bundled_res_dir = executable_dir / "resources"

            self.BASE_DIR = self._resolve_writable_base_dir()
        else:
            self.BASE_DIR = Path(__file__).resolve().parents[1]
            self._bundled_res_dir = self.BASE_DIR / "resources"
            self._doc_search_dirs = [self.BASE_DIR]

        self.TEMP_DIR = self.BASE_DIR / "temp"
        self.OUTPUT_DIR = self.BASE_DIR / "output"
        self.LOG_DIR = self.BASE_DIR / "logs"
        self.CONFIG_FILE = self.BASE_DIR / "config.json"

        # 初始化必要目录
        self._init_dirs()
        self.RES_DIR = self._load_resource_dir()

    def _init_dirs(self):
        """确保临时/输出/日志目录存在"""
        for path in [self.TEMP_DIR, self.OUTPUT_DIR, self.LOG_DIR]:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass

    def _resolve_writable_base_dir(self) -> Path:
        system_name = platform.system()
        candidates = []

        if system_name == "Windows":
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                candidates.append(Path(local_app_data) / "PhisperLite")
            candidates.append(Path.home() / "AppData" / "Local" / "PhisperLite")
        elif system_name == "Darwin":
            candidates.append(Path.home() / "Library" / "Application Support" / "PhisperLite")

        candidates.extend([
            Path.home() / ".phisperlite",
            Path(tempfile.gettempdir()) / "PhisperLite",
        ])

        for candidate in candidates:
            if self._is_writable_directory(candidate):
                return candidate

        return candidates[-1]

    def _is_writable_directory(self, path: Path) -> bool:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return True
        except OSError:
            return False

    def _load_settings(self) -> dict:
        if not self.CONFIG_FILE.exists():
            return {}
        try:
            return json.loads(self.CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_settings(self, settings: dict):
        try:
            self.CONFIG_FILE.write_text(
                json.dumps(settings, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _load_resource_dir(self) -> Path:
        settings = self._load_settings()
        configured_dir = settings.get("resource_dir", "").strip()
        if configured_dir:
            resource_dir = Path(configured_dir).expanduser()
            if resource_dir.exists():
                return resource_dir
        return self._bundled_res_dir or (self.BASE_DIR / "resources")

    def set_resource_dir(self, resource_dir: str):
        target = Path(resource_dir).expanduser().resolve()
        self.RES_DIR = target
        settings = self._load_settings()
        settings["resource_dir"] = str(target)
        self._save_settings(settings)

    def clear_resource_dir(self):
        self.RES_DIR = self._bundled_res_dir or (self.BASE_DIR / "resources")
        settings = self._load_settings()
        settings.pop("resource_dir", None)
        self._save_settings(settings)

    def get_resource_dir(self) -> str:
        return str(self.RES_DIR)

    def get_resource_status(self) -> tuple[bool, list[str]]:
        missing_items = []
        resource_dir = self.RES_DIR

        if not resource_dir.exists():
            return False, [f"资源目录不存在: {resource_dir}"]

        if not Path(self.ffmpeg_bin).exists():
            missing_items.append("缺少 ffmpeg")
        if not Path(self.whisper_cli).exists():
            missing_items.append("缺少 whisper-cli")
        if not Path(self.whisper_model_path).exists():
            missing_items.append("缺少 ggml-large-v3-turbo.bin")

        translator_candidates = []
        if self.hunyuan_model_path:
            translator_candidates.append("hunyuan")
        if self.qwen_model_path:
            translator_candidates.append("qwen")

        if not translator_candidates:
            missing_items.append("至少需要一个翻译模型（Hunyuan 或完整 Qwen 分片）")

        return not missing_items, missing_items

    def get_resource_status_text(self) -> str:
        is_ready, missing_items = self.get_resource_status()
        if is_ready:
            return f"资源目录就绪: {self.RES_DIR}"
        return "资源未就绪: " + "；".join(missing_items)
    @property
    def llm_model_path(self) -> str:
        """兼容旧调用：默认返回混元模型路径"""
        return self.get_llm_model_path("hunyuan")
    @property
    def ffmpeg_bin(self) -> str:
        """定位FFmpeg可执行文件（自动适配系统并处理Unix执行权限）"""
        sys_name = platform.system()
        ext = ".exe" if sys_name == "Windows" else ""
        local_path = self.RES_DIR / "ffmpeg" / f"ffmpeg{ext}"
        
        # 兼容你结构图中 resources/ffmpeg 或 resources/ffmpeg.exe 的写法
        if not local_path.exists():
            local_path = self.RES_DIR / f"ffmpeg{ext}"

        if local_path.exists():
            if sys_name != "Windows" and not os.access(local_path, os.X_OK):
                try:
                    os.chmod(local_path, 0o755)
                except Exception:
                    pass
            return str(local_path)
        return "ffmpeg"

    @property
    def whisper_cli(self) -> str:
        """定位whisper-cli可执行文件"""
        ext = ".exe" if platform.system() == "Windows" else ""
        target = self.RES_DIR / f"whisper-cli{ext}"
        return str(target) if target.exists() else f"whisper-cli{ext}"

    @property
    def whisper_model_path(self) -> str:
        """定位Whisper模型文件 (ggml格式)"""
        model_name = "ggml-large-v3-turbo.bin"
        target = self.RES_DIR / model_name
        return str(target) if target.exists() else model_name

    @property
    def hunyuan_model_path(self) -> str:
        """定位混元 (Hunyuan-MT) 模型文件 (GGUF格式)"""
        model_name = "Hunyuan-MT-7B-q4_k_m.gguf"
        target = self.RES_DIR / model_name
        # 如果模型在特定子目录下，可修改为 self.RES_DIR / "hunyuan" / model_name
        return str(target) if target.exists() else ""

    @property
    def qwen_model_path(self) -> str:
        """定位千问 (Qwen) GGUF 模型入口文件"""
        part1 = self.RES_DIR / "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
        part2 = self.RES_DIR / "qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf"
        return str(part1) if part1.exists() and part2.exists() else ""

    def get_llm_model_path(self, backend: str) -> str:
        """按翻译模型类型返回对应的本地模型路径"""
        backend_key = (backend or "").strip().lower()
        if backend_key == "qwen":
            return self.qwen_model_path
        if backend_key == "hunyuan":
            return self.hunyuan_model_path
        return ""

    def get_translator_display_name(self, backend: str) -> str:
        """返回翻译模型的展示名称"""
        return self.TRANSLATOR_BACKENDS.get((backend or "").strip().lower(), backend or "未知模型")

    def get_available_translator_backends(self) -> list[tuple[str, str]]:
        """返回当前已配置可选的翻译模型列表"""
        backends = []
        for backend, label in self.TRANSLATOR_BACKENDS.items():
            if self.get_llm_model_path(backend):
                backends.append((backend, label))
        return backends

    @property
    def nllb_model_dir(self) -> str:
        """定位NLLB翻译模型目录 (作为备选翻译方案)"""
        target = self.RES_DIR / "nllb_1.3b_ct2"
        return str(target) if target.exists() else ""

    def get_temp_path(self, filename: str) -> str:
        """生成临时文件路径"""
        return str(self.TEMP_DIR / filename)

    def get_default_browse_dir(self) -> str:
        """返回文件选择器的默认目录。"""
        if getattr(sys, "frozen", False):
            return str(Path.home())
        return str(self.BASE_DIR)

    def get_icon_candidates(self) -> list[Path]:
        """Return icon candidates in platform-preferred order."""
        system_name = platform.system()
        if system_name == "Darwin":
            names = ["icon.icns", "icon.png", "icon.ico", "favicon-2.ico"]
        elif system_name == "Windows":
            names = ["favicon-2.ico", "icon.ico", "icon.png", "icon.icns"]
        else:
            names = ["icon.png", "favicon-2.ico", "icon.ico", "icon.icns"]
        return [self.RES_DIR / name for name in names]

    def get_readme_path(self, prefer_english: bool = False) -> str:
        preferred_names = ["README.en.md", "README.md"] if prefer_english else ["README.md", "README.en.md"]
        fallback_names = ["WINDOWS_MACOS_NOTES.md"]
        checked_dirs = []

        for base_dir in self._doc_search_dirs + [self.BASE_DIR]:
            if base_dir in checked_dirs:
                continue
            checked_dirs.append(base_dir)

            for name in preferred_names + fallback_names:
                candidate = base_dir / name
                if candidate.exists():
                    return str(candidate)

        return ""

# 全局配置单例
config = PhisperConfig()

# 配置自检模块
if __name__ == "__main__":
    print("\n" + "="*60)
    print(f"🔍 PhisperLite 路径环境检查 (System: {platform.system()})")
    print("="*60)
    
    # 定义检查项：(显示名称, 路径值, 是否为核心必选)
    check_items = [
        ("项目根目录", str(config.BASE_DIR), True),
        ("资源总目录", str(config.RES_DIR), True),
        ("FFmpeg 路径", config.ffmpeg_bin, True),
        ("Whisper 程序", config.whisper_cli, True),
        ("Whisper 模型", config.whisper_model_path, True),
        ("混元模型 (GGUF)", config.hunyuan_model_path, True),
        ("千问模型 (GGUF)", config.qwen_model_path, False),
        ("NLLB 模型目录", config.nllb_model_dir, False),
        ("临时文件夹", str(config.TEMP_DIR), True),
    ]

    critical_missing = False
    
    for name, path, is_critical in check_items:
        exists = os.path.exists(path) if path else False
        
        # 状态图标逻辑
        if exists:
            status_icon = "✅ 正常"
        else:
            if is_critical:
                status_icon = "❌ 缺失 (核心资源)"
                # 排除系统环境变量中可能存在的命令
                if "ffmpeg" not in name.lower() and "Whisper 程序" not in name:
                    critical_missing = True
            else:
                status_icon = "⚠️  未找到 (可选资源)"
        
        print(f"{name:<15}: {path if path else '未定义'}")
        print(f"{'':<17}状态: {status_icon}")
        print("-" * 55)

    print("\n" + "="*60)
    if not critical_missing:
        print("🚀 [READY] 混元模型及核心环境已就绪，可以开始处理！")
    else:
        print("🛑 [ERROR] 缺少核心模型或程序，请检查 resources 目录。")
        print("提示：请确保 Hunyuan-MT-7B-q4_k_m.gguf 放在 resources/ 下")
    print("="*60 + "\n")
