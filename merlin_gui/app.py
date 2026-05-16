"""Entry point for the Merlin GUI editor."""

from __future__ import annotations

import os
import sys

# Silence Qt's multimedia info log about its bundled ffmpeg.
os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.ffmpeg.info=false")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QFontDatabase  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from .main_window import MainWindow  # noqa: E402
from .styles import apply_theme  # noqa: E402


def main() -> int:
    QApplication.setAttribute(Qt.AA_DontShowIconsInMenus, False)
    app = QApplication(sys.argv)
    app.setApplicationName("Merlin Editor")
    app.setApplicationDisplayName("Merlin Editor")

    system_font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
    system_font.setPointSize(13)
    app.setFont(system_font)

    apply_theme(app)

    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
