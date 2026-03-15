import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


class SafeConsoleHandler(logging.StreamHandler):
    """Fallback to replacement characters when the console encoding cannot print some Unicode."""

    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            try:
                msg = self.format(record)
                encoding = getattr(self.stream, "encoding", None) or "utf-8"
                safe_msg = msg.encode(encoding, errors="replace").decode(encoding, errors="replace")
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)


def setup_logger(name="Phisper"):
    # 1. 获取项目根目录下的 logs 文件夹（从 config 导入或直接计算）
    # 这里我们直接根据文件位置计算，确保 logger 模块独立
    try:
        # 正常作为包运行时的导入
        from utils.config import config
    except (ImportError, ModuleNotFoundError):
        # 直接运行此文件调试时的补救措施
        
        # 将当前 logger.py 的上级目录（即项目根目录）加入搜索路径
        root_path = str(Path(__file__).resolve().parents[1])
        if root_path not in sys.path:
            sys.path.append(root_path)
        # 再次尝试导入
        from config import config
    log_file = config.LOG_DIR / "phisper.log"

    # 2. 创建 Logger 实例
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 防止重复添加 Handler（防止在多次调用 setup_logger 时日志翻倍）
    if logger.hasHandlers():
        return logger

    # 3. 定义日志格式
    # 时间 | 级别 | 模块 | 消息
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 4. 控制台 Handler (Stdout)
    console_handler = SafeConsoleHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # 控制台通常只看 INFO 级别
    console_handler.setFormatter(formatter)

    # 5. 文件 Handler (RotatingFileHandler - 自动滚动更新，限制日志体积)
    # 当前日志文件控制在约 100KB，额外保留 1 个备份文件
    file_handler = None
    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=100 * 1024, backupCount=1, encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG) # 文件里保存最详尽的 DEBUG 信息
        file_handler.setFormatter(formatter)
    except OSError as exc:
        console_handler.setLevel(logging.DEBUG)
        console_handler.stream.write(f"[Phisper] 文件日志不可用，已退回控制台日志: {exc}\n")
        console_handler.flush()

    # 6. 添加 Handler
    logger.addHandler(console_handler)
    if file_handler is not None:
        logger.addHandler(file_handler)

    return logger

# 全局默认 logger
logger = setup_logger()

# --- 测试模块 ---
if __name__ == "__main__":
    logger.info("Logger 模块初始化成功！")
    logger.debug("这是一条调试信息，仅在文件和 Debug 模式可见。")
    logger.error("模拟报错信息测试。")
