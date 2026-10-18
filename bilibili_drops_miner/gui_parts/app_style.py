from __future__ import annotations

import sys
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

APP_STYLE_SHEET = """
QWidget { background: transparent; color: #18191c; font-size: 13px; }
QMainWindow, QDialog, QScrollArea, QWidget#workspace { background: #f6f7f8; }
QLabel { background: transparent; }
QLabel[role="muted"] { color: #61666d; }
QLabel[role="pageTitle"] { font-size: 25px; font-weight: 700; color: #18191c; }
QFrame#sidebar { background: #f1f2f3; border-right: 1px solid #e3e5e7; }
QFrame#card, QFrame#settingsGroup { background: #ffffff; border: 1px solid #e3e5e7; border-radius: 12px; }
QFrame#hero { background: #ffffff; border: 1px solid #e3e5e7; border-radius: 12px; }
QPushButton { background: #ffffff; color: #35383f; border: 1px solid #e3e5e7; border-radius: 7px; padding: 8px 14px; min-height: 18px; font-weight: 500; }
QPushButton:hover { background: #f6f7f8; border-color: #c9ccd0; }
QPushButton:pressed { background: #edeef0; }
QPushButton:focus { border: 1px solid #a92d56; }
QPushButton:disabled { color: #9499a0; background: #f1f2f3; border-color: #e3e5e7; }
QPushButton#nav { text-align: left; background: transparent; color: #61666d; border: 1px solid transparent; padding: 10px 12px; border-radius: 7px; }
QPushButton#nav:hover { background: #e9ebee; color: #18191c; }
QPushButton#nav:checked { background: #fff0f5; color: #a92d56; font-weight: 600; border-color: #f5c6d7; }
QPushButton#nav:focus { border-color: #d64873; }
QPushButton#textButton { background: transparent; color: #a92d56; border: 0; padding: 6px 8px; }
QPushButton#textButton:hover { background: #fff0f5; }
QLineEdit, QComboBox { background: #ffffff; color: #35383f; border: 1px solid #e3e5e7; border-radius: 7px; padding: 8px 11px; min-height: 18px; selection-background-color: #fbd8e5; selection-color: #18191c; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #fb7299; background: #fffcfd; }
QLineEdit:disabled, QComboBox:disabled { color: #9499a0; background: #f1f2f3; }
QComboBox::drop-down { border: 0; width: 22px; }
QComboBox QAbstractItemView { background: white; color: #35383f; border: 1px solid #e3e5e7; selection-background-color: #e9f7fc; selection-color: #a92d56; padding: 6px; }
QTabWidget::pane { border: 1px solid #e3e5e7; background: #f6f7f8; border-radius: 8px; }
QTabBar::tab { background: transparent; color: #61666d; padding: 10px 22px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #a92d56; border-bottom: 2px solid #fb7299; font-weight: 600; }
QTabBar::tab:hover { color: #18191c; background: #f1f2f3; }
QTableWidget { background: white; alternate-background-color: #fcfcfd; border: 0; gridline-color: #edeef0; selection-background-color: #fff2f6; selection-color: #18191c; outline: 0; }
QTableWidget::item { padding: 10px; border-bottom: 1px solid #edeef0; }
QHeaderView::section { background: #f8f9fa; color: #61666d; border: 0; border-bottom: 1px solid #e3e5e7; padding: 10px; font-size: 13px; font-weight: 500; }
QTableCornerButton::section { background: #f8f9fa; border: 0; }
QPlainTextEdit { background: #ffffff; color: #61666d; border: 1px solid #e3e5e7; border-radius: 8px; padding: 10px; selection-background-color: #fbd8e5; }
QCheckBox { spacing: 9px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #b2b6bc; background: #fff; }
QCheckBox::indicator:checked { background: #fb7299; border: 3px solid #a92d56; }
QCheckBox:focus { color: #a92d56; }
QProgressBar { background: #edeef0; border: 0; border-radius: 3px; min-height: 4px; max-height: 4px; }
QProgressBar::chunk { background: #fb7299; border-radius: 3px; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #d5d7db; border-radius: 3px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: #bfc3c9; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 2px; }
QScrollBar::handle:horizontal { background: #d5d7db; border-radius: 3px; min-width: 28px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
QMenu, QToolTip { background: white; color: #35383f; border: 1px solid #e3e5e7; padding: 6px; border-radius: 6px; }
QMenu::item { padding: 8px 20px; border-radius: 4px; }
QMenu::item:selected { background: #e9f7fc; }
"""

def configure_qt_app(app: QApplication) -> None:
    app.setStyle("Fusion")
    family = {"win32": "Microsoft YaHei UI", "darwin": "PingFang SC"}.get(sys.platform, "Noto Sans CJK SC")
    if family not in QFontDatabase.families():
        family = "Segoe UI"
    font = QFont(family, 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    palette = QPalette()
    for role, color in (
        (QPalette.Window, "#f6f7f8"), (QPalette.WindowText, "#18191c"),
        (QPalette.Base, "#ffffff"), (QPalette.AlternateBase, "#fcfcfd"),
        (QPalette.Text, "#18191c"), (QPalette.Button, "#ffffff"),
        (QPalette.ButtonText, "#35383f"), (QPalette.Highlight, "#fbd8e5"),
        (QPalette.HighlightedText, "#18191c"), (QPalette.PlaceholderText, "#9499a0"),
    ):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(APP_STYLE_SHEET)
