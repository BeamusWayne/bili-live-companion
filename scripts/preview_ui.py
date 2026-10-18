"""Offline visual review with explicitly synthetic data; never logs in or watches."""
from __future__ import annotations

import argparse
import gc
import os
from pathlib import Path
import sys
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from bilibili_drops_miner.client_parts.models import TaskProgress, TaskCheckpointProgress
from bilibili_drops_miner.credential_store import MemoryCredentialStore
from bilibili_drops_miner.domain import ApplicationState, RuntimeHealth, TaskSnapshot
from bilibili_drops_miner.gui_parts import main_window
from bilibili_drops_miner.gui_parts.app_style import configure_qt_app
from bilibili_drops_miner.gui_parts.cookie_profiles import CookieProfileState


def main():
    global app, window  # Keep Qt owners alive through interpreter teardown.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    # The offscreen Windows platform does not enumerate installed system fonts.
    if sys.platform == "win32":
        for filename in ("msyh.ttc", "msyhbd.ttc", "segoeui.ttf", "seguisb.ttf", "consola.ttf"):
            QFontDatabase.addApplicationFont(str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / filename))
    configure_qt_app(app)
    with patch.object(main_window, "JsonCredentialStore", MemoryCredentialStore), \
         patch.object(main_window, "load_cookie_profile_state", lambda **kwargs: CookieProfileState([])), \
         patch.object(main_window, "save_cookie_profiles", lambda *args, **kwargs: None), \
         patch.object(main_window.MinerGUI, "_setup_system_tray", lambda self: None), \
         patch.object(main_window.MinerGUI, "_check_update_silent", lambda self: None):
        window = main_window.MinerGUI()
        gc.collect()
        for timer in window.findChildren(QTimer):
            timer.stop()
        window.show()
        app.processEvents()
        window.grab().save(str(args.output / "workspace-empty.png"))
        window.rooms_edit.setText("23612045")
        window.cookie_profile_combo.setItemText(window.cookie_profile_combo.currentIndex(), "主账号 · 演示数据")
        snapshot = TaskSnapshot(progresses=(TaskProgress(
            "preview", "守望先锋 · 直播观看任务", 1, 75, 120, check_points=[
                TaskCheckpointProgress("a", "观看 30 分钟", 3, 30, 30, "活动奖励", 1),
                TaskCheckpointProgress("b", "观看 60 分钟", 3, 60, 60, "活动奖励", 1),
                TaskCheckpointProgress("c", "观看 90 分钟", 1, 75, 90, "活动奖励", 1),
                TaskCheckpointProgress("d", "观看 120 分钟", 1, 75, 120, "活动奖励", 1),
            ]),))
        window._render_task_snapshot(snapshot)
        window._render_runtime_health(RuntimeHealth(state=ApplicationState.RUNNING, active_sessions=2, target_sessions=2, concurrency_mode="automatic", concurrency_phase="steady"))
        window.runtime_detail_label.setText("演示数据 · 自动稳定模式")
        window.cookie_profile_combo.setItemText(window.cookie_profile_combo.currentIndex(), "主账号 · 界面演示")
        window.start_btn.setText("停止")
        window.start_btn.setEnabled(True)
        window._set_action_button_color(window.start_btn, "red")
        app.processEvents()
        window.grab().save(str(args.output / "workspace-preview.png"))
        window._set_application_state(ApplicationState.IDLE)
        window.workspace_pages.setCurrentIndex(1)
        app.processEvents()
        window.grab().save(str(args.output / "accounts-preview.png"))
        window.settings_dialog.show()
        app.processEvents()
        window.settings_dialog.grab().save(str(args.output / "settings-preview.png"))
        # Avoid persisting synthetic state or starting the event loop.
        window._exit_requested = True
        window.settings_dialog.close()
        window.close()
        gc.collect()


if __name__ == "__main__":
    main()
