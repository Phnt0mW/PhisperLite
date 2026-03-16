import subprocess
import re
import os
import sys
import time
import logging
import platform
from pathlib import Path
from typing import Callable, List, Tuple

# --- 运行时动态路径补丁 ---
ROOT_DIR = str(Path(__file__).resolve().parents[1])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.base import TaskStep
from utils.config import config
from utils.logger import logger

class WhisperWorker(TaskStep):
    def run(self, wav_path: str, progress_cb: Callable[[float], None]) -> str:
        """
        核心任务：调用 whisper-cli 进行语音识别，支持断点续跑和内存无缝拼接。
        """
        model_path = config.whisper_model_path
        total_duration = self._get_wav_duration(wav_path)
        self.logger.info(f"🚀 启动 Whisper 识别 | 模型: {os.path.basename(model_path)} | 总时长: {total_duration:.2f}s")

        current_offset_ms = 0
        # 核心数据结构升级：存储格式为 (start_ms: int, end_ms: int, text: str)
        parsed_segments: List[Tuple[int, int, str]] = [] 
        
        max_retries = 5
        retry_count = 0

        while current_offset_ms < (total_duration * 1000) and retry_count < max_retries:
            if self._is_aborted:
                self.logger.warning("任务被用户中止。")
                break

            cmd = self._build_command(wav_path, current_offset_ms)
            self.logger.debug(f"启动/重启进程 | 当前起点 Offset: {current_offset_ms}ms")

            # 启动进程，使用 bufsize=1 实现实时行缓冲
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True, 
                bufsize=1,
                encoding='utf-8', 
                errors='replace'
            )

            # 进入流监控循环
            needs_restart, next_offset_ms = self._monitor_process(
                process, total_duration, progress_cb, parsed_segments
            )

            if needs_restart:
                retry_count += 1
                current_offset_ms = next_offset_ms
                self.logger.warning(f"⚠️ 触发自愈机制 ({retry_count}/{max_retries}) | 回退至安全起点: {current_offset_ms/1000:.2f}s")
                time.sleep(1.5)  # 给予硬件短暂冷却与释放资源的时间
            else:
                self.logger.info("进程正常结束，未触发死循环或崩溃。")
                break

        self.logger.info(f"✅ Whisper 识别闭环 | 最终获取有效字幕行数: {len(parsed_segments)}")
        
        # 结果处理：生成纯文本和 SRT 文件
        final_text = "\n".join([seg[2] for seg in parsed_segments])
        
        if parsed_segments:
            srt_output_path = str(Path(wav_path).with_suffix('.srt'))
            self._save_as_srt(parsed_segments, srt_output_path)
            self.logger.info(f"📄 标准 SRT 字幕已生成至: {srt_output_path}")
            
        return final_text

    def _build_command(self, wav_path: str, offset_ms: int) -> list:
        """构造 whisper.cpp 的底层执行命令"""
        beam_size, best_of = self._resolve_decode_params()
        cmd = [
            config.whisper_cli,
            "-m", config.whisper_model_path,
            "-f", wav_path,
            "-l", "auto",
                      
            "--offset-t", str(offset_ms),
            "--beam-size", str(beam_size),
            "--best-of", str(best_of),
            "--entropy-thold", "2.4",
            "--logprob-thold", "-1.0",
            "--no-speech-thold", "0.6",
            "--max-len", "80"
        ]

        thread_count = self._resolve_thread_count()
        if thread_count > 0:
            cmd.extend(["-t", str(thread_count)])

        return cmd

    def _resolve_thread_count(self) -> int:
        configured_value = os.environ.get("PHISPER_WHISPER_THREADS", "").strip()
        if configured_value:
            try:
                return max(1, int(configured_value))
            except ValueError:
                self.logger.warning(f"忽略无效的 PHISPER_WHISPER_THREADS: {configured_value}")

        cpu_count = os.cpu_count() or 1
        if platform.system() == "Windows":
            return max(1, cpu_count - 1)
        return max(1, cpu_count // 2)

    def _resolve_decode_params(self) -> Tuple[int, int]:
        beam_size = self._resolve_positive_int_env("PHISPER_WHISPER_BEAM_SIZE")
        best_of = self._resolve_positive_int_env("PHISPER_WHISPER_BEST_OF")
        if beam_size and best_of:
            return beam_size, best_of

        if platform.system() == "Windows":
            return 2, 2
        return 5, 5

    def _resolve_positive_int_env(self, env_name: str) -> int:
        configured_value = os.environ.get(env_name, "").strip()
        if not configured_value:
            return 0

        try:
            return max(1, int(configured_value))
        except ValueError:
            self.logger.warning(f"忽略无效的 {env_name}: {configured_value}")
            return 0

    def _monitor_process(self, process: subprocess.Popen, total_duration: float, 
                         progress_cb: Callable[[float], None], parsed_segments: List[Tuple[int, int, str]]) -> Tuple[bool, int]:
        """
        实时监控控制台输出流。
        :return: (是否需要重启: bool, 下一次启动的 offset_ms: int)
        """
        last_log_progress = -0.1
        last_timestamp_ms = 0 if not parsed_segments else parsed_segments[-1][1]
        
        # 预编译正则，提升循环内匹配性能
        # 匹配: [00:00:10.500 --> 00:00:12.000] 文本内容
        pattern = re.compile(r"\[(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\]\s*(.*)")

        try:
            for line in process.stdout:
                if self._is_aborted:
                    return False, last_timestamp_ms

                clean_line = line.strip()
                if not clean_line:
                    continue

                # 完整输出 Debug 日志
                self.logger.debug(f"[CLI] {clean_line}")

                match = pattern.search(clean_line)
                if match:
                    start_ms = self._timestamp_to_ms(match.group(1))
                    end_ms = self._timestamp_to_ms(match.group(2))
                    text_content = match.group(3).strip()

                    last_timestamp_ms = end_ms
                    parsed_segments.append((start_ms, end_ms, text_content))

                    # 进度条派发逻辑
                    if total_duration > 0:
                        progress = min(end_ms / (total_duration * 1000), 1.0)
                        progress_cb(progress)
                        if progress - last_log_progress >= 0.05:
                            self.logger.info(f"⏳ 识别进度: {progress*100:.1f}%")
                            last_log_progress = progress

                    # --- 核心死循环 / 幻听检测 ---
                    # 检查最后 3 条记录是否文本完全相同
                    if len(parsed_segments) >= 3:
                        last_3_texts = [seg[2] for seg in parsed_segments[-3:]]
                        if len(set(last_3_texts)) == 1 and bool(last_3_texts[0]):
                            self.logger.error(f"🛑 侦测到模型死循环 (重复文本: '{last_3_texts[0]}')")
                            
                            # 获取第一句重复台词的起始时间，往前退 100ms
                            first_repeat_start_ms = parsed_segments[-3][0]
                            restart_offset = max(0, first_repeat_start_ms - 100)
                            
                            # 剔除这 3 句被污染的重复数据，保证内存绝对干净
                            del parsed_segments[-3:]
                            
                            process.terminate()
                            return True, restart_offset

                else:
                    # 捕获并记录潜在的引擎报错
                    if any(kw in clean_line.lower() for kw in ["error", "fail", "warning"]):
                        self.logger.warning(f"[CLI 内部警告] {clean_line}")

            process.wait()
            
            # 异常退出但未被死循环捕获的处理
            if process.returncode != 0 and not self._is_aborted:
                self.logger.error(f"❌ 进程非正常退出 (Return Code: {process.returncode})")
                return True, last_timestamp_ms

        except Exception as e:
            self.logger.error(f"🔥 流监控发生异常: {e}", exc_info=True)
            process.terminate()
            return True, last_timestamp_ms
        finally:
            # 确保无论由于什么原因跳出，进程资源都被彻底释放
            if process.poll() is None:
                process.terminate()
                process.wait()

        return False, last_timestamp_ms

    def _save_as_srt(self, segments: List[Tuple[int, int, str]], out_path: str):
        """将结构化的内存数据迅速转换为标准 SRT 格式文件"""
        with open(out_path, "w", encoding="utf-8") as f:
            for i, (start_ms, end_ms, text) in enumerate(segments, 1):
                start_str = self._ms_to_srt_time(start_ms)
                end_str = self._ms_to_srt_time(end_ms)
                f.write(f"{i}\n{start_str} --> {end_str}\n{text}\n\n")

    def _timestamp_to_ms(self, ts_str: str) -> int:
        """[00:00:10.500] 格式转毫秒"""
        h, m, s = ts_str.split(':')
        s, ms = s.split('.')
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

    def _ms_to_srt_time(self, ms: int) -> str:
        """毫秒转 SRT 标准时间格式 00:00:00,000"""
        h = ms // 3600000
        ms %= 3600000
        m = ms // 60000
        ms %= 60000
        s = ms // 1000
        ms %= 1000
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _get_wav_duration(self, wav_path: str) -> float:
        """调用 FFmpeg 获取音频精确时长"""
        try:
            cmd = [config.ffmpeg_bin, "-i", wav_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            match = re.search(r"Duration:\s(\d+):(\d+):(\d+\.\d+)", result.stderr)
            if match:
                h, m, s = map(float, match.groups())
                return h * 3600 + m * 60 + s
        except Exception as e:
            self.logger.warning(f"获取音频时长失败: {e}")
        return 0.0

# --- 本地测试沙盒 ---
if __name__ == "__main__":
    # 强制开启 DEBUG 日志以便观察底层执行
    logger.setLevel(logging.DEBUG)
    worker = WhisperWorker()

    def on_progress(p):
        print(f"\r[外围监控] 识别进度: {p*100:.2f}%", end="", flush=True)

    test_wav = str(Path(ROOT_DIR) / "temp" / "temp_audio.wav")
    
    if os.path.exists(test_wav):
        print("="*60)
        print("🚀 开始进行 Whisper 核心逻辑沙盒测试")
        print("="*60)
        
        start_time = time.time()
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        
        # 执行识别任务
        final_text = worker.run(test_wav, on_progress)
        
        # 控制台简要输出
        print("\n\n" + "-"*30 + " 纯文本结果预览 " + "-"*30)
        print(final_text[:600] + ("\n\n... (后续截断)" if len(final_text) > 600 else ""))
        
        # 文件归档与防覆盖逻辑
        output_dir = Path(ROOT_DIR) / "temp" / "test_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        txt_path = output_dir / f"whisper_result_{timestamp_str}.txt"
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(final_text)
            
        elapsed = time.time() - start_time
        
        print("\n" + "="*60)
        print(f"🎉 测试圆满完成！")
        print(f"⏱️  总耗时: {elapsed:.2f} 秒")
        print(f"📄 归档纯文本: {txt_path}")
        print(f"🎬 归档字幕文件 (SRT): {Path(test_wav).with_suffix('.srt')}")
        print("="*60)
        
    else:
        print(f"❌ 未找到测试音频，请检查路径: {test_wav}")
