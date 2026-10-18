from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def show_update_available_dialog(
    parent: QWidget,
    *,
    app_version: str,
    latest_version: str,
    release_url: str,
) -> bool:
    dialog = QDialog(parent)
    dialog.setWindowTitle("发现新版本")
    dialog.setModal(True)
    dialog.setMinimumWidth(430)
    dialog.setStyleSheet(
        "QDialog{background:#f6f7f8;color:#18191c;}"
        "QLabel{color:#18191c;}"
        "QPushButton{background:#ffffff;color:#18191c;border:1px solid #e3e5e7;"
        "border-radius:6px;padding:8px 18px;min-width:92px;}"
        "QPushButton:hover{background:#fff0f5;border-color:#fb7299;}"
        "QPushButton#primary{background:#fb7299;color:#4c2031;border-color:#fb7299;}"
        "QPushButton#primary:hover{background:#ff8fb0;}"
    )

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 22, 24, 20)
    layout.setSpacing(14)

    title = QLabel(f"发现新版本 {latest_version}")
    title_font = QFont()
    title_font.setPointSize(14)
    title_font.setBold(True)
    title.setFont(title_font)
    layout.addWidget(title)

    body = QLabel(
        f"当前版本：{app_version}\n"
        "发布仓库：github.com/BeamusWayne/bili-live-companion\n"
        "可前往发布页下载最新版本。"
    )
    body.setWordWrap(True)
    body.setStyleSheet("color:#61666d;line-height:1.45;")
    layout.addWidget(body)

    button_row = QHBoxLayout()
    button_row.addStretch(1)
    later_btn = QPushButton("稍后")
    open_btn = QPushButton("打开发布页")
    open_btn.setObjectName("primary")
    later_btn.clicked.connect(dialog.reject)
    open_btn.clicked.connect(dialog.accept)
    button_row.addWidget(later_btn)
    button_row.addWidget(open_btn)
    layout.addLayout(button_row)

    return dialog.exec() == QDialog.Accepted
