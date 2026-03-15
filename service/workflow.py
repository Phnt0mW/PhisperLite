import os
import shutil
from pathlib import Path
from enum import Enum
from typing import Callable, Optional

# 引入项目根目录补丁（如果在 UI 层已经处理过，这里可以省略）
import sys
ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.ffmpeg import FFmpegWorker
from core.whisper import WhisperWorker
from core.translator import TranslatorWorker
from utils.config import config
from utils.logger import logger

class WorkflowState(Enum):
    """严谨的工作流状态枚举"""
    IDLE = "空闲准备"
    EXTRACTING_AUDIO = "提取音轨"
    TRANSCRIBING = "语音识别"
    TRANSLATING = "智能翻译"
    COMPLETED = "任务完成"
    ERROR = "发生错误"
    ABORTED = "任务中止"

class PhisperWorkflow:
    def __init__(self):
        # 实例化核心流水线工序
        self.ffmpeg_worker = FFmpegWorker()
        self.whisper_worker = WhisperWorker()
        self.translator_worker = TranslatorWorker()
        
        # 流程控制变量
        self.current_worker = None
        self._is_aborted = False
        self.current_state = WorkflowState.IDLE

    def start_pipeline(
        self,
        video_path: str,
        progress_callback: Callable[[WorkflowState, float, str], None],
        translator_backend: str = "hunyuan",
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """
        启动完整的音视频处理与翻译流水线。
        """
        self._is_aborted = False
        self.current_state = WorkflowState.IDLE
        translator_backend = (translator_backend or "hunyuan").strip().lower()
        translator_name = config.get_translator_display_name(translator_backend)
        
        # 记录需要被清理的临时文件
        temp_files_to_clean = []
        
        # 基于原视频计算目标输出路径
        video_path_obj = Path(video_path)
        output_dir = self._resolve_output_dir(video_path_obj)
        target_srt_path = str(output_dir / f"{video_path_obj.stem}.srt")
        target_bilingual_srt_path = str(output_dir / f"{video_path_obj.stem}.translated.srt")

        final_results = {
            "success": False,
            "audio_path": "", # 音频作为临时文件会被删掉，最终无需提供此路径
            "srt_path": "",
            "bilingual_srt_path": "",
            "error_msg": ""
        }

        try:
            logger.info(f"🎬 [Workflow] 开始处理文件: {video_path_obj.name}")

            # ==========================================
            # 阶段 1: 提取音频 (Video -> temp_audio.wav)
            # ==========================================
            self._set_state(WorkflowState.EXTRACTING_AUDIO, 0.0, "正在提取高音质音轨...", progress_callback)
            self.current_worker = self.ffmpeg_worker
            
            wav_path = self.ffmpeg_worker.run(
                video_path, 
                lambda p: progress_callback(self.current_state, p, "FFmpeg 提取中...")
            )
            
            self._check_abort()
            if not wav_path or not os.path.exists(wav_path):
                raise RuntimeError("音频提取失败，未生成临时 wav 文件。")
            
            # 标记为待清理
            temp_files_to_clean.append(wav_path)
            logger.info(f"✅ [Workflow] 音频提取完成 (临时存放在: {wav_path})")

            # ==========================================
            # 阶段 2: 语音识别 (Wav -> temp_audio.srt -> 目标文件夹)
            # ==========================================
            self._set_state(WorkflowState.TRANSCRIBING, 0.0, "加载 Whisper 模型，准备识别...", progress_callback)
            self.current_worker = self.whisper_worker
            
            self.whisper_worker.run(
                wav_path, 
                lambda p: progress_callback(self.current_state, p, "Whisper 语音转写中...")
            )
            
            self._check_abort()
            # Whisper 生成的临时 srt 文件
            temp_srt_path = str(Path(wav_path).with_suffix('.srt'))
            if not os.path.exists(temp_srt_path):
                raise RuntimeError("语音识别完成，但未能找到生成的临时 SRT 文件。")
            temp_files_to_clean.append(temp_srt_path)
            shutil.copyfile(temp_srt_path, target_srt_path)
            final_results["srt_path"] = target_srt_path
            logger.info(f"✅ [Workflow] 原始字幕已生成至源目录: {target_srt_path}")

            # ==========================================
            # 阶段 3: 智能翻译 (目标文件夹的 SRT -> 双语 SRT)
            # ==========================================
            self._set_state(WorkflowState.TRANSLATING, 0.0, f"唤醒{translator_name}模型，开始双语翻译...", progress_callback)
            self.current_worker = self.translator_worker
            
            # 直接传入已经转移好的 target_srt_path
            # TranslatorWorker 内部逻辑会自动在同级目录下生成 .zh-jp.srt
            bilingual_srt_path = self.translator_worker.run(
                target_srt_path,
                lambda p: progress_callback(self.current_state, p, f"{translator_name}模型翻译中..."),
                backend=translator_backend,
                log_cb=log_callback,
            )
            
            self._check_abort()
            if not bilingual_srt_path or not os.path.exists(bilingual_srt_path):
                raise RuntimeError("翻译过程似乎已结束，但未能生成双语字幕文件。")

            if bilingual_srt_path != target_bilingual_srt_path:
                shutil.move(bilingual_srt_path, target_bilingual_srt_path)

            final_results["bilingual_srt_path"] = target_bilingual_srt_path
            logger.info(f"✅ [Workflow] 双语字幕已生成: {target_bilingual_srt_path}")

            if os.path.exists(target_srt_path):
                os.remove(target_srt_path)
                final_results["srt_path"] = ""
                logger.info(f"🧹 [Workflow] 已清理中间字幕文件: {target_srt_path}")

            # ==========================================
            # 流程完美结束
            # ==========================================
            self._set_state(WorkflowState.COMPLETED, 1.0, "全部处理完成！", progress_callback)
            final_results["success"] = True
            self.current_worker = None
            return final_results

        except InterruptedError as e:
            self._set_state(WorkflowState.ABORTED, 0.0, "任务已被用户取消。", progress_callback)
            final_results["error_msg"] = str(e)
            return final_results
            
        except Exception as e:
            logger.error(f"❌ [Workflow] 发生致命错误: {e}", exc_info=True)
            self._set_state(WorkflowState.ERROR, 0.0, f"发生错误: {str(e)}", progress_callback)
            final_results["error_msg"] = str(e)
            return final_results
            
        finally:
            # ✨ 核心优化：强制清场机制
            # 无论成功、失败还是中止，只要跳出 try 块，必定执行此清理逻辑
            self._cleanup_temp_files(temp_files_to_clean)
            self._reset_temp_workspace()

    def _cleanup_temp_files(self, file_paths: list):
        """静默清理不再需要的临时文件"""
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    logger.debug(f"🧹 已清理临时文件: {path}")
                except Exception as e:
                    logger.warning(f"⚠️ 清理临时文件失败 {path}: {e}")

    def _reset_temp_workspace(self):
        """清空整个临时工作目录，避免遗留中间文件影响下次任务"""
        temp_dir = config.TEMP_DIR
        if not temp_dir.exists():
            return

        try:
            shutil.rmtree(temp_dir)
            logger.debug(f"🧹 已重置临时目录: {temp_dir}")
        except Exception as e:
            logger.warning(f"⚠️ 重置临时目录失败 {temp_dir}: {e}")
        finally:
            temp_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_output_dir(self, video_path: Path) -> Path:
        preferred_dir = video_path.parent
        if self._is_writable_directory(preferred_dir):
            return preferred_dir

        fallback_dir = config.OUTPUT_DIR
        fallback_dir.mkdir(parents=True, exist_ok=True)
        logger.warning(f"⚠️ 源文件目录不可写，字幕将输出到: {fallback_dir}")
        return fallback_dir

    def _is_writable_directory(self, directory: Path) -> bool:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            probe = directory / ".phisper_write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return True
        except OSError:
            return False

    def abort(self):
        """供 UI 线程调用的硬中止接口"""
        logger.warning("🛑 [Workflow] 接收到全局中止指令！")
        self._is_aborted = True
        if self.current_worker:
            self.current_worker.abort()

    def _set_state(self, state: WorkflowState, progress: float, msg: str, cb: Callable[[WorkflowState, float, str], None]):
        """内部状态机切换与广播辅助函数"""
        self.current_state = state
        cb(self.current_state, progress, msg)

    def _check_abort(self):
        """在每个大工序交接处，再次确认是否被中止"""
        if self._is_aborted:
            raise InterruptedError("工作流被强行中断。")

# --- 本地联调测试 ---
if __name__ == "__main__":
    def mock_ui_receiver(state: WorkflowState, progress: float, msg: str):
        print(f"\r【UI 渲染】状态: {state.value} | 进度: {progress*100:5.1f}% | 提示: {msg}", end="")

    workflow = PhisperWorkflow()
    
    # 请确保此文件存在，测试完后去它的目录下看看是不是多出了同名的 srt 文件！
    test_video = str(Path(ROOT_DIR) / "Taylor Swift - Love Story.mp3")
    
    if os.path.exists(test_video):
        print("🚀 开始进行完整的 Workflow 串联测试...")
        result = workflow.start_pipeline(test_video, mock_ui_receiver, translator_backend="hunyuan")
        
        print("\n\n" + "="*50)
        print("📋 最终输出报告:")
        for k, v in result.items():
            print(f" - {k}: {v}")
        print("="*50)
    else:
        print(f"找不到测试文件: {test_video}，请调整路径。")
