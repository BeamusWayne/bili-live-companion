from urllib.parse import parse_qs, urlsplit
import pytest
from bilibili_drops_miner.downloader_bridge import build_handoff, normalize_video
from bilibili_drops_miner.progress_confirmation import ProgressConfirmation
from bilibili_drops_miner.domain import TaskSnapshot
from bilibili_drops_miner.client_parts.models import TaskProgress


def test_handoff_is_public_deduplicated_and_retains_parts():
    uri, links = build_handoff("BV1SUnB61E8K\nhttps://www.bilibili.com/video/BV1SUnB61E8K/?vd_source=x\nhttps://www.bilibili.com/video/BV1SUnB61E8K?p=2")
    assert len(links) == 2
    assert parse_qs(urlsplit(uri).query) == {"url": links}
    assert "vd_source" not in uri
    assert links[-1].endswith("?p=2")


@pytest.mark.parametrize("value", ["https://live.bilibili.com/23612045", "https://www.bilibili.com.evil/video/BV1SUnB61E8K", "file:///C:/secret", "https://u:p@www.bilibili.com/video/BV1SUnB61E8K", "bilidownloader://download?url=x", "https://www.bilibili.com/video/BV1SUnB61E8K?p=-1", "https://www.bilibili.com:99/video/BV1SUnB61E8K"])
def test_reject_unsupported_handoff(value):
    with pytest.raises(ValueError):
        normalize_video(value)


def test_heartbeat_and_optimistic_claim_cannot_confirm_server_growth():
    state = ProgressConfirmation()
    def snapshot(value, at, **kwargs):
        return TaskSnapshot(progresses=(TaskProgress("t", "任务", 1, value, 100),), refreshed_at=at, **kwargs)
    state.observe(snapshot(2, 100), running=True)
    state.observe(snapshot(99, 101, server_confirmed=False), running=True)
    assert state.last_growth == 0
    for at in (130,160,190):
        state.observe(snapshot(2, at), running=True)
    assert "3 次未增长" in state.label(now=191,interval=30)
    state.observe(snapshot(3,220),running=True)
    assert "确认进度增长" in state.label(now=221,interval=30)
    assert "已过期" in state.label(now=400,interval=30)
    state.observe(TaskSnapshot(error="network",refreshed_at=500),running=True)
    assert state.last_sync == 220


def test_dialog_handoff_and_missing_app_fallback(monkeypatch):
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit, QPushButton, QWidget
    from bilibili_drops_miner import downloader_bridge as bridge
    app = QApplication.instance() or QApplication([])
    owner = QWidget()
    urls = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda u: urls.append(u.toString()) or True)
    monkeypatch.setattr(bridge, "is_installed", lambda: True)

    def send():
        dialog = app.activeModalWidget()
        dialog.findChild(QPlainTextEdit).setPlainText("BV1SUnB61E8K")
        next(b for b in dialog.findChildren(QPushButton) if b.text() == "在下载器中确认").click()

    QTimer.singleShot(0, send)
    bridge.open_download_dialog(owner)
    assert urls and urls[0].startswith("bilidownloader://download?url=")
    monkeypatch.setattr(bridge, "is_installed", lambda: False)

    def missing():
        dialog = app.activeModalWidget()
        dialog.findChild(QPlainTextEdit).setPlainText("BV1SUnB61E8K")
        next(b for b in dialog.findChildren(QPushButton) if b.text() == "在下载器中确认").click()
        assert any("尚未找到下载器" in l.text() for l in dialog.findChildren(QLabel))
        dialog.reject()

    QTimer.singleShot(0, missing)
    bridge.open_download_dialog(owner)
    assert len(urls) == 1
    owner.close()
