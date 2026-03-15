from PySide6.QtCore import QObject, Signal, Slot

from service.workflow import PhisperWorkflow


class WorkflowWorker(QObject):
    progress_changed = Signal(str, int, str)
    log_message = Signal(str)
    finished = Signal(dict)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self._workflow = PhisperWorkflow()
        self._cancel_requested = False

    @Slot(str, str)
    def process(self, video_path: str, translator_backend: str):
        self._cancel_requested = False
        self.log_message.emit(f"开始处理: {video_path}")
        self.log_message.emit(f"翻译模型: {translator_backend}")

        try:
            result = self._workflow.start_pipeline(
                video_path,
                self._handle_progress,
                translator_backend=translator_backend,
                log_callback=self.log_message.emit,
            )

            if result.get("success"):
                self.log_message.emit("处理完成。")
                self.finished.emit(result)
            elif self._cancel_requested:
                self.log_message.emit("任务已取消。")
                self.cancelled.emit()
            else:
                error_msg = result.get("error_msg") or "处理失败。"
                self.log_message.emit(f"处理失败: {error_msg}")
                self.failed.emit(error_msg)
        except Exception as exc:
            error_msg = str(exc)
            self.log_message.emit(f"运行异常: {error_msg}")
            self.failed.emit(error_msg)

    @Slot()
    def cancel(self):
        self._cancel_requested = True
        self.log_message.emit("正在取消任务...")
        self._workflow.abort()

    def _handle_progress(self, state, progress: float, message: str):
        progress_value = max(0, min(int(progress * 100), 100))
        self.progress_changed.emit(state.value, progress_value, message)
