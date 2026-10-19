import logging
from typing import Any, Callable

class TaskStep:
    """
    处理步骤基类
    FFmpeg、Whisper 和 Translator 等处理步骤均继承此类。
    """
    def __init__(self):
        # 控制开关：用于从外部（如点击取消按钮）停止当前耗时任务
        self._is_aborted = False
        # 日志记录器：子类可以直接使用 self.logger 发射日志
        self.logger = logging.getLogger(f"Phisper.{self.__class__.__name__}")

    def run(self, input_data: Any, progress_cb: Callable[[float], None]) -> Any:
        """
        核心执行逻辑
        
        :param input_data: 上一个处理步骤输出的数据（可能是文件路径，也可能是文本列表）
        :param progress_cb: 进度回调函数，接收一个 0.0 到 1.0 之间的 float
        :return: 处理后的数据，将作为下一个处理步骤的 input_data
        """
        raise NotImplementedError("子类必须实现 run 方法")

    def abort(self):
        """
        中止任务
        在子类的循环或阻塞逻辑中，应不断检查 self._is_aborted 状态
        """
        self._is_aborted = True
        self.logger.warning("任务收到中止指令。")

    def check_aborted(self):
        """
        任务已中止时抛出 InterruptedError
        """
        if self._is_aborted:
            raise InterruptedError("任务已被用户中止。")
