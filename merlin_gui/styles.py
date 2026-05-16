"""macOS-style QSS stylesheets for light and dark mode."""

from __future__ import annotations

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication


LIGHT_QSS = """
QMainWindow {
    background: #ECECEC;
    color: #1C1C1E;
}

QToolBar {
    background: #ECECEC;
    border: none;
    border-bottom: 1px solid #D7D7D7;
    padding: 8px 12px;
    spacing: 6px;
}

QToolBar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px 10px;
    color: #1C1C1E;
}
QToolBar QToolButton:hover    { background: rgba(0,0,0,0.06); }
QToolBar QToolButton:pressed  { background: rgba(0,0,0,0.10); }
QToolBar QToolButton:disabled { color: #B0B0B5; }

#sidebar {
    background: #F2F2F2;
    border-right: 1px solid #D7D7D7;
}

#sidebarBottomBar {
    background: #F2F2F2;
    border-top: 1px solid #DEDEDE;
}

#sidebarBottomBar QPushButton {
    background: transparent;
    border: none;
    color: #3C3C43;
    font-size: 16px;
    padding: 6px 10px;
    border-radius: 4px;
    min-width: 24px;
}
#sidebarBottomBar QPushButton:hover    { background: rgba(0,0,0,0.06); }
#sidebarBottomBar QPushButton:pressed  { background: rgba(0,0,0,0.10); }
#sidebarBottomBar QPushButton:disabled { color: #C7C7CC; }

QTreeWidget {
    background: transparent;
    border: none;
    outline: none;
    show-decoration-selected: 1;
}
QTreeWidget::item {
    padding: 5px 6px;
    border-radius: 4px;
}
QTreeWidget::item:hover            { background: rgba(0,0,0,0.04); }
QTreeWidget::item:selected         { background: rgba(0,122,255,0.18); color: #1C1C1E; }
QTreeWidget::item:selected:active  { background: #007AFF; color: white; }
QTreeWidget::branch { background: transparent; }
QTreeWidget::branch:selected:active { background: #007AFF; }
QHeaderView::section {
    background: transparent;
    border: none;
    padding: 6px;
    color: #6C6C70;
    font-size: 11px;
}

QStackedWidget#detail, QFrame#detailEditor, QFrame#detailEmpty {
    background: #FFFFFF;
}

#sectionHeader {
    color: #6C6C70;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.6px;
}

#emptyState {
    color: #8E8E93;
    font-size: 15px;
}

#imageFrame {
    background: #F5F5F7;
    border: 1px solid #E5E5EA;
    border-radius: 14px;
}

#titleEdit {
    background: #FFFFFF;
    border: 1px solid #D1D1D6;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 15px;
}
#titleEdit:focus { border: 1px solid #007AFF; }

#audioRow {
    background: #F5F5F7;
    border: 1px solid #E5E5EA;
    border-radius: 10px;
    padding: 8px 12px;
}

QPushButton#playButton {
    background: #FFFFFF;
    border: 1px solid #D1D1D6;
    border-radius: 16px;
    font-size: 14px;
    padding: 0;
}
QPushButton#playButton:hover   { background: #F0F0F2; }
QPushButton#playButton:pressed { background: #E0E0E5; }

#timeLabel {
    color: #6C6C70;
    font-size: 12px;
}

QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #D1D1D6;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #007AFF;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 1px solid #C7C7CC;
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover { border-color: #007AFF; }

QPushButton {
    background: #FFFFFF;
    border: 1px solid #D1D1D6;
    border-radius: 7px;
    padding: 6px 14px;
    color: #1C1C1E;
}
QPushButton:hover    { background: #F5F5F7; }
QPushButton:pressed  { background: #E8E8ED; }
QPushButton:disabled { color: #C7C7CC; background: #FAFAFA; border-color: #E5E5EA; }

QPushButton#primary {
    background: #007AFF;
    color: white;
    border: 1px solid #006FE5;
}
QPushButton#primary:hover   { background: #0A84FF; }
QPushButton#primary:pressed { background: #0066D9; }

QPushButton#linkButton {
    background: transparent;
    border: none;
    color: #007AFF;
    padding: 4px 0;
    text-align: left;
}
QPushButton#linkButton:hover { color: #0A84FF; text-decoration: underline; }

QStatusBar {
    background: #ECECEC;
    color: #6C6C70;
    border-top: 1px solid #D7D7D7;
}

QSplitter::handle { background: transparent; width: 1px; }
"""


DARK_QSS = """
QMainWindow {
    background: #1E1E1E;
    color: #F2F2F7;
}

QToolBar {
    background: #2A2A2C;
    border: none;
    border-bottom: 1px solid #3A3A3C;
    padding: 8px 12px;
    spacing: 6px;
}
QToolBar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px 10px;
    color: #F2F2F7;
}
QToolBar QToolButton:hover    { background: rgba(255,255,255,0.08); }
QToolBar QToolButton:pressed  { background: rgba(255,255,255,0.12); }
QToolBar QToolButton:disabled { color: #5A5A5F; }

#sidebar {
    background: #232325;
    border-right: 1px solid #3A3A3C;
}

#sidebarBottomBar {
    background: #232325;
    border-top: 1px solid #3A3A3C;
}
#sidebarBottomBar QPushButton {
    background: transparent;
    border: none;
    color: #D1D1D6;
    font-size: 16px;
    padding: 6px 10px;
    border-radius: 4px;
    min-width: 24px;
}
#sidebarBottomBar QPushButton:hover   { background: rgba(255,255,255,0.08); }
#sidebarBottomBar QPushButton:pressed { background: rgba(255,255,255,0.12); }
#sidebarBottomBar QPushButton:disabled{ color: #5A5A5F; }

QTreeWidget {
    background: transparent;
    border: none;
    outline: none;
    show-decoration-selected: 1;
}
QTreeWidget::item {
    padding: 5px 6px;
    border-radius: 4px;
}
QTreeWidget::item:hover            { background: rgba(255,255,255,0.06); }
QTreeWidget::item:selected         { background: rgba(10,132,255,0.28); color: #FFFFFF; }
QTreeWidget::item:selected:active  { background: #0A84FF; color: white; }
QTreeWidget::branch { background: transparent; }
QTreeWidget::branch:selected:active { background: #0A84FF; }
QHeaderView::section {
    background: transparent;
    border: none;
    padding: 6px;
    color: #8E8E93;
    font-size: 11px;
}

QStackedWidget#detail, QFrame#detailEditor, QFrame#detailEmpty {
    background: #1E1E1E;
}

#sectionHeader {
    color: #8E8E93;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.6px;
}

#emptyState {
    color: #8E8E93;
    font-size: 15px;
}

#imageFrame {
    background: #2C2C2E;
    border: 1px solid #3A3A3C;
    border-radius: 14px;
}

#titleEdit {
    background: #2C2C2E;
    border: 1px solid #3A3A3C;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 15px;
    color: #F2F2F7;
}
#titleEdit:focus { border: 1px solid #0A84FF; }

#audioRow {
    background: #2C2C2E;
    border: 1px solid #3A3A3C;
    border-radius: 10px;
    padding: 8px 12px;
}

QPushButton#playButton {
    background: #3A3A3C;
    border: 1px solid #48484A;
    border-radius: 16px;
    font-size: 14px;
    padding: 0;
    color: #F2F2F7;
}
QPushButton#playButton:hover   { background: #48484A; }
QPushButton#playButton:pressed { background: #54545A; }

#timeLabel {
    color: #8E8E93;
    font-size: 12px;
}

QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #3A3A3C;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #0A84FF;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #F2F2F7;
    border: 1px solid #48484A;
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover { border-color: #0A84FF; }

QPushButton {
    background: #3A3A3C;
    border: 1px solid #48484A;
    border-radius: 7px;
    padding: 6px 14px;
    color: #F2F2F7;
}
QPushButton:hover    { background: #48484A; }
QPushButton:pressed  { background: #54545A; }
QPushButton:disabled { color: #5A5A5F; background: #2C2C2E; border-color: #3A3A3C; }

QPushButton#primary {
    background: #0A84FF;
    color: white;
    border: 1px solid #006FE5;
}
QPushButton#primary:hover   { background: #1E90FF; }
QPushButton#primary:pressed { background: #0066D9; }

QPushButton#linkButton {
    background: transparent;
    border: none;
    color: #0A84FF;
    padding: 4px 0;
    text-align: left;
}
QPushButton#linkButton:hover { color: #1E90FF; text-decoration: underline; }

QStatusBar {
    background: #2A2A2C;
    color: #8E8E93;
    border-top: 1px solid #3A3A3C;
}

QSplitter::handle { background: transparent; width: 1px; }
"""


def is_dark_mode(app: QApplication) -> bool:
    bg = app.palette().color(QPalette.Window)
    return bg.lightnessF() < 0.5


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(DARK_QSS if is_dark_mode(app) else LIGHT_QSS)


def detail_bg_color() -> str:
    """Background for the detail panel — must be set inline because Qt's
    QSS does not cascade reliably into QStackedWidget children."""
    return "#1E1E1E" if is_dark_mode(QApplication.instance()) else "#FFFFFF"
