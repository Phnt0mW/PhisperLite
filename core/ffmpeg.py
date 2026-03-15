import subprocess
import re
import os
from typing import Callable
from core.base import TaskStep
from utils.config import config
from utils.logger import logger

class FFmpegWorker(TaskStep):
    def run(self, video_path: str, progress_cb: Callable[[float], None]) -> str:
        """
        核心任务：提取音频并转换为 16k/单声道/wav 格式
        :param video_path: 输入视频的绝对路径
        :param progress_cb: 回调函数，用于发射 0.0 ~ 1.0 的进度
        :return: 生成的临时 wav 文件路径
        """
        # 1. 准备输出路径（通过 config 获取临时文件夹路径）
        output_wav = config.get_temp_path("temp_audio.wav")
        
        # 2. 获取视频总时长 (用于换算百分比)
        duration = self._get_duration(video_path)
        self.logger.info(f"开始音轨提取任务: {os.path.basename(video_path)}")
        self.logger.info(f"媒体总时长: {duration}s")

        # 3. 构造 FFmpeg 命令
        # -y: 覆盖输出; -i: 输入文件; -ar: 16k采样率; -ac: 单声道; -vn: 禁用视频流
        cmd = [
            config.ffmpeg_bin, "-y", "-i", video_path,
            "-ar", "16000", "-ac", "1", "-vn", output_wav
        ]
        self.logger.debug(f"执行 FFmpeg 命令: {' '.join(cmd)}")

        # 4. 启动进程 (隐藏控制台窗口并在后台运行)
        # 移除 universal_newlines，改用 bytes 读取后解码，避免自动换行符处理冲突
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            encoding='utf-8'  # 直接指定编码，替代 universal_newlines
        )

        try:
            # 进度日志计数器：每10%进度才记录一次，减少日志量
            last_log_progress = -0.1
            
            # 5. 实时读取输出行（修复版：状态过滤+轻量化处理）
            for line in process.stdout:
                # 优先检查中止标志，减少无效处理
                if self._is_aborted:
                    process.terminate()
                    self.logger.warning("用户中止了 FFmpeg 进程。")
                    return ""

                # --- 核心修复：轻量级清洗，不拆分内部字符 ---
                # 只清理两端的回车、换行、空格，保留行内完整内容
                clean_line = line.strip('\r\n ')
                if not clean_line:
                    continue

                # --- 日志分级记录：抓大放小 ---
                if "time=" in clean_line:
                    # 进度行：降低日志频率（每10%进度记录一次）
                    match = re.search(r"time=(\d+):(\d+):(\d+.\d+)", clean_line)
                    if match and duration > 0:
                        h, m, s = map(float, match.groups())
                        current_time = h * 3600 + m * 60 + s
                        progress = min(current_time / duration, 1.0)
                        
                        # 每10%进度记录一次日志，避免刷屏
                        if progress - last_log_progress >= 0.1:
                            self.logger.debug(f"[FFmpeg Progress] 进度: {progress*100:.1f}% | {clean_line}")
                            last_log_progress = progress
                elif any(keyword in clean_line.lower() for keyword in ["error", "warning", "fail"]):
                    # 错误/警告行：重点记录（升级为warning级别）
                    self.logger.warning(f"[FFmpeg Alert]: {clean_line}")
                elif any(keyword in clean_line for keyword in ["Stream mapping", "Input #", "Output #", "Duration"]):
                    # 关键信息行：完整记录
                    self.logger.debug(f"[FFmpeg Info]: {clean_line}")
                # 其他高频进度行：不记录，只用于UI进度更新

                # 解析进度并回调（核心功能不受日志影响）
                match = re.search(r"time=(\d+):(\d+):(\d+.\d+)", clean_line)
                if match and duration > 0:
                    h, m, s = map(float, match.groups())
                    current_time = h * 3600 + m * 60 + s
                    progress = min(current_time / duration, 1.0)
                    progress_cb(progress)

            # 等待进程结束并获取退出码
            process.wait()

            if process.returncode == 0:
                self.logger.info(f"音频提取成功: {output_wav}")
                return output_wav
            else:
                self.logger.error(f"FFmpeg 执行出错，退出码: {process.returncode}")
                return ""

        except Exception as e:
            self.logger.error(f"FFmpeg 处理异常: {str(e)}", exc_info=True)
            return ""

    def _get_duration(self, file_path: str) -> float:
        """
        通过尝试打开文件获取媒体时长
        """
        try:
            cmd = [config.ffmpeg_bin, "-i", file_path]
            self.logger.debug(f"获取媒体时长命令: {' '.join(cmd)}")
            
            # 执行命令，超时10秒保护
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                timeout=10
            )
            
            # 处理时长解析的日志（同样抓大放小）
            for line in result.stderr.split('\n'):
                clean_line = line.strip('\r\n ')
                if not clean_line:
                    continue
                    
                if "Duration:" in clean_line:
                    self.logger.debug(f"[FFmpeg Duration]: {clean_line}")
                elif "error" in clean_line.lower():
                    self.logger.warning(f"[FFmpeg Duration Alert]: {clean_line}")

            # 解析时长
            match = re.search(r"Duration:\s(\d+):(\d+):(\d+.\d+)", result.stderr)
            if match:
                h, m, s = map(float, match.groups())
                total_seconds = h * 3600 + m * 60 + s
                self.logger.debug(f"解析出媒体时长: {total_seconds} 秒")
                return total_seconds
            else:
                self.logger.warning("未从 FFmpeg 输出中解析到媒体时长")
                
        except subprocess.TimeoutExpired:
            self.logger.error("获取媒体时长超时（10秒）")
        except Exception as e:
            self.logger.warning(f"无法获取视频时长: {str(e)}")
        return 0.0

# --- 本地测试模块 ---
if __name__ == "__main__":
    # 使用方法示例
    worker = FFmpegWorker()
    
    # 模拟 UI 的进度回调
    def on_progress(p):
        print(f"\r[测试进度]: {p*100:.2f}%", end="")

    # 请确保 resources/ 下有 ffmpeg，并在下面填入一个存在的视频路径
    test_video = "test.mp4" 
    if os.path.exists(test_video):
        result = worker.run(test_video, on_progress)
        print(f"\n最终输出文件: {result}")
    else:
        print(f"\n未找到测试视频 {test_video}，请修改代码中的 test_video 路径。")
