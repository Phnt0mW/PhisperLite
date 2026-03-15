from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils.config import config
from ui.icons import get_app_icon, get_app_pixmap
from ui.worker import WorkflowWorker


class MainWindow(QMainWindow):
    start_requested = Signal(str, str)
    cancel_requested = Signal()

    def __init__(self):
        super().__init__()
        self._thread = None
        self._worker = None

        self.setWindowTitle("PhisperLite by Phnt0mW")
        self.setWindowIcon(get_app_icon())
        self.resize(640, 420)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("请选择一个音频或视频文件")

        self.resource_input = QLineEdit()
        self.resource_input.setReadOnly(True)
        self.resource_input.setPlaceholderText("请选择 resources 文件夹")

        self.translator_combo = QComboBox()
        self._translator_options = []

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setPixmap(get_app_pixmap(72))

        self.browse_button = QPushButton("浏览")
        self.resource_button = QPushButton("选择资源目录")
        self.check_resource_button = QPushButton("检查资源")
        self.start_button = QPushButton("开始处理")
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setEnabled(False)

        self.status_label = QLabel("等待开始")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("运行日志会显示在这里")

        top_row = QHBoxLayout()
        top_row.addWidget(self.path_input)
        top_row.addWidget(self.browse_button)

        resource_row = QHBoxLayout()
        resource_row.addWidget(self.resource_input)
        resource_row.addWidget(self.resource_button)
        resource_row.addWidget(self.check_resource_button)

        translator_row = QHBoxLayout()
        translator_row.addWidget(QLabel("翻译模型"))
        translator_row.addWidget(self.translator_combo)

        button_row = QHBoxLayout()
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(self.icon_label)
        layout.addLayout(top_row)
        layout.addLayout(resource_row)
        layout.addLayout(translator_row)
        layout.addLayout(button_row)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_output)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.browse_button.clicked.connect(self._browse_file)
        self.resource_button.clicked.connect(self._choose_resource_dir)
        self.check_resource_button.clicked.connect(self._check_resource_dir)
        self.start_button.clicked.connect(self._start_processing)
        self.cancel_button.clicked.connect(self._cancel_processing)

        self._refresh_resource_state()
        self._ensure_resource_dir_on_startup()

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择媒体文件",
            config.get_default_browse_dir(),
            "Media Files (*.mp3 *.wav *.m4a *.mp4 *.mkv *.mov *.avi);;All Files (*)",
        )
        if file_path:
            self.path_input.setText(file_path)

    def _choose_resource_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择 resources 文件夹",
            config.get_default_browse_dir(),
        )
        if not directory:
            return

        config.set_resource_dir(directory)
        self._refresh_resource_state()
        self._check_resource_dir(show_success=True)

    def _check_resource_dir(self, show_success: bool = False):
        is_ready, missing_items = config.get_resource_status()
        if is_ready:
            self._append_log(f"资源目录检查通过: {config.get_resource_dir()}")
            if show_success:
                self._show_message("information", "资源检查", "资源目录检查通过。")
            return True

        message = "资源目录不完整：\n" + "\n".join(missing_items)
        self._append_log(message)
        self._show_message("warning", "资源检查", message)
        return False

    def _ensure_resource_dir_on_startup(self):
        if config.get_resource_status()[0]:
            return

        self._append_log("当前资源目录未就绪，请先选择 resources 文件夹。")
        self._show_message(
            "information",
            "配置资源目录",
            "首次使用或资源未就绪，请先选择 resources 文件夹。",
        )

    def _refresh_resource_state(self):
        self.resource_input.setText(config.get_resource_dir())
        self.setWindowIcon(get_app_icon())
        self.icon_label.setPixmap(get_app_pixmap(72))
        self._reload_translator_options()
        self.status_label.setText(config.get_resource_status_text())
        self.start_button.setEnabled(config.get_resource_status()[0] and self._thread is None)

    def _reload_translator_options(self):
        current_backend = self.translator_combo.currentData()
        self.translator_combo.clear()

        self._translator_options = config.get_available_translator_backends()
        for backend, label in self._translator_options:
            self.translator_combo.addItem(label, backend)

        if current_backend:
            index = self.translator_combo.findData(current_backend)
            if index >= 0:
                self.translator_combo.setCurrentIndex(index)

    def _start_processing(self):
        file_path = self.path_input.text().strip()
        if not file_path:
            self._show_message("warning", "提示", "请先选择文件。")
            return

        if not config.get_resource_status()[0]:
            self._show_message("warning", "提示", "请先配置可用的 resources 文件夹。")
            return

        if self._thread is not None:
            self._show_message("information", "提示", "当前已有任务在运行。")
            return

        self.progress_bar.setValue(0)
        self.status_label.setText("准备开始")
        self.log_output.clear()
        self._append_log(f"已选择文件: {file_path}")
        backend = self.translator_combo.currentData()
        backend_label = self.translator_combo.currentText()
        self._append_log(f"已选择翻译模型: {backend_label}")
        self._set_running_state(True)

        self._thread = QThread(self)
        self._worker = WorkflowWorker()
        self._worker.moveToThread(self._thread)

        self.start_requested.connect(self._worker.process)
        self.cancel_requested.connect(self._worker.cancel)

        self._thread.finished.connect(self._thread.deleteLater)
        self._worker.progress_changed.connect(self._on_progress_changed)
        self._worker.log_message.connect(self._append_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._worker.cancelled.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)

        self._thread.start()
        self.start_requested.emit(file_path, backend)

    def _cancel_processing(self):
        if self._worker is not None:
            self.cancel_requested.emit()

    def _on_progress_changed(self, state_text: str, progress_value: int, message: str):
        self.status_label.setText(f"{state_text} | {message}")
        self.progress_bar.setValue(progress_value)
        self._append_log(f"[{state_text}] {message} ({progress_value}%)")

    def _on_finished(self, result: dict):
        self._set_running_state(False)
        output_path = result.get("bilingual_srt_path", "")
        self.status_label.setText("处理完成")
        self.progress_bar.setValue(100)
        self._append_log(f"输出文件: {output_path}")
        self._show_message("information", "完成", f"字幕已生成：\n{output_path}")

    def _on_failed(self, error_message: str):
        self._set_running_state(False)
        self.status_label.setText("处理失败")
        self._show_message("critical", "失败", error_message)

    def _on_cancelled(self):
        self._set_running_state(False)
        self.status_label.setText("任务已取消")
        self._show_message("information", "取消", "任务已取消。")

    def _cleanup_worker(self):
        if self._worker is not None:
            try:
                self.start_requested.disconnect(self._worker.process)
            except (TypeError, RuntimeError):
                pass
            try:
                self.cancel_requested.disconnect(self._worker.cancel)
            except (TypeError, RuntimeError):
                pass
            self._worker.deleteLater()

        self._worker = None
        self._thread = None

    def _set_running_state(self, is_running: bool):
        self.start_button.setEnabled((not is_running) and config.get_resource_status()[0])
        self.browse_button.setEnabled(not is_running)
        self.resource_button.setEnabled(not is_running)
        self.check_resource_button.setEnabled(not is_running)
        self.translator_combo.setEnabled(not is_running)
        self.cancel_button.setEnabled(is_running)

    def _append_log(self, message: str):
        self.log_output.appendPlainText(message)

    def _show_message(self, level: str, title: str, text: str):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.setWindowIcon(get_app_icon())

        if level == "warning":
            box.setIcon(QMessageBox.Warning)
        elif level == "critical":
            box.setIcon(QMessageBox.Critical)
        else:
            box.setIcon(QMessageBox.Information)

        box.exec()
