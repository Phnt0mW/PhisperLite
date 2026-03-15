from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt

from utils.config import config


def get_app_icon() -> QIcon:
    icon_path = config.RES_DIR / "favicon-2.ico"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


def get_app_pixmap(size: int = 96) -> QPixmap:
    icon_path = config.RES_DIR / "favicon-2.ico"
    if not icon_path.exists():
        return QPixmap()

    pixmap = QPixmap(str(icon_path))
    return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
