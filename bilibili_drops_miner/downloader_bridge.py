"""Public video handoff. Never transfer cookies, tokens, room ids or commands."""
from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit

PROJECT_URL = "https://github.com/BeamusWayne/bilibili-video-downloader/releases"


def normalize_video(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"BV[A-Za-z0-9]{10}|av[0-9]+", value):
        value = f"https://www.bilibili.com/video/{value}"
    u = urlsplit(value)
    if (u.scheme not in {"http", "https"} or u.hostname not in {"bilibili.com", "www.bilibili.com"}
            or u.username or u.password or u.port not in {None, 80, 443}
            or not re.fullmatch(r"/video/(BV[A-Za-z0-9]{10}|av[0-9]+)/?", u.path)):
        raise ValueError("请粘贴已发布视频的 BV/AV 链接，直播间链接不能作为回放下载。")
    result = f"https://www.bilibili.com{u.path.rstrip('/')}"
    part = dict(parse_qsl(u.query)).get("p")
    if part is not None:
        if not part.isascii() or not part.isdigit() or not 1 <= int(part) <= 5000:
            raise ValueError("分 P 序号应为 1–5000。")
        result += f"?p={int(part)}"
    return result


def build_handoff(text: str) -> tuple[str, list[str]]:
    lines = [v.strip() for v in text.splitlines() if v.strip()]
    if not 1 <= len(lines) <= 100:
        raise ValueError("每行一个视频链接，一次可发送 1–100 条。")
    links = list(dict.fromkeys(normalize_video(v) for v in lines))
    uri = "bilidownloader://download?" + urlencode([("url", v) for v in links])
    if len(uri) > 32768:
        raise ValueError("链接总长度过大，请分批发送。")
    return uri, links


def is_installed() -> bool:
    import sys
    if sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\bilidownloader\shell\open\command") as key:
                return bool(winreg.QueryValueEx(key, "")[0])
        except OSError:
            return False
    # macOS Launch Services owns URL registration; openUrl reports launch failure.
    return True


def open_download_dialog(parent) -> None:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout
    dialog = QDialog(parent)
    dialog.setWindowTitle("下载回放 / 相关视频")
    dialog.resize(560, 340)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(16)
    layout.addWidget(QLabel("回放发布后，粘贴 BV 链接并交给下载器确认。"))
    editor = QPlainTextEdit()
    editor.setAccessibleName("回放视频链接")
    editor.setPlaceholderText("每行一个 BV/AV 号或视频链接")
    layout.addWidget(editor, 1)
    status = QLabel("")
    status.setWordWrap(True)
    status.setStyleSheet("color:#b2781a;")
    layout.addWidget(status)
    buttons = QHBoxLayout()
    install = QPushButton("获取下载器 ↗")
    install.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PROJECT_URL)))
    buttons.addWidget(install)
    copy = QPushButton("复制视频链接")
    buttons.addWidget(copy)
    buttons.addStretch()
    send = QPushButton("在下载器中确认")
    send.setStyleSheet("background:#fb7299;color:white;border:0;border-radius:8px;padding:10px 16px;")
    buttons.addWidget(send)
    layout.addLayout(buttons)

    def submit(*, clipboard: bool = False) -> None:
        try:
            uri, links = build_handoff(editor.toPlainText())
        except ValueError as exc:
            status.setText(str(exc))
            return
        if clipboard:
            QApplication.clipboard().setText("\n".join(links))
            status.setText("已复制，可粘贴到下载器的新建页面。")
        elif not is_installed() or not QDesktopServices.openUrl(QUrl(uri)):
            status.setText("尚未找到下载器。请先安装，或复制链接后在下载器中粘贴。")
        else:
            dialog.accept()

    copy.clicked.connect(lambda: submit(clipboard=True))
    send.clicked.connect(lambda: submit())
    dialog.exec()
