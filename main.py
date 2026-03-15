import sys

from PySide6.QtWidgets import QApplication

from ui.icons import get_app_icon
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setWindowIcon(get_app_icon())
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
