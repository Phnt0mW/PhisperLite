from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt

from utils.config import config


def _get_existing_icon_path():
    for icon_path in config.get_icon_candidates():
        if icon_path.exists():
            return icon_path
    return None


def get_app_icon() -> QIcon:
    icon_path = _get_existing_icon_path()
    if icon_path is not None:
        return QIcon(str(icon_path))
    return QIcon()


def get_app_pixmap(size: int = 96) -> QPixmap:
    icon_path = _get_existing_icon_path()
    if icon_path is None:
        return QPixmap()

    pixmap = QPixmap(str(icon_path))
    return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
