"""Offline integration check used by the Windows release build."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
from zoneinfo import ZoneInfo


def run_desktop_smoke_test() -> int:
    global _smoke_app, _smoke_window
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from bilibili_drops_miner.credential_store import JsonCredentialStore
    from bilibili_drops_miner._version import APP_VERSION
    from bilibili_drops_miner.gui_parts.app_style import configure_qt_app
    from bilibili_drops_miner.gui_parts.main_window import MinerGUI
    from bilibili_drops_miner.gui_parts.window_chrome import bundled_resource_path, install_window_chrome

    class SmokeWindow(MinerGUI):
        def _setup_system_tray(self):
            pass

        def _check_update_silent(self):
            pass

    result = {"ok": False, "version": APP_VERSION, "checks": []}
    previous_data_dir = os.environ.get("BILIDROP_DATA_DIR")
    with tempfile.TemporaryDirectory(prefix="bilidrop-smoke-") as data_dir:
        os.environ["BILIDROP_DATA_DIR"] = data_dir
        try:
            if ZoneInfo("Asia/Shanghai").key != "Asia/Shanghai":
                raise RuntimeError("Missing timezone data")
            result["checks"].append("timezone")
            store = JsonCredentialStore()
            if sys.platform == "win32":
                store.set("smoke", "offline-test-credential")
                if store.get("smoke") != "offline-test-credential":
                    raise RuntimeError("DPAPI round trip failed")
                store.delete("smoke")
                result["checks"].append("dpapi")
            _smoke_app = QApplication.instance() or QApplication([])
            configure_qt_app(_smoke_app)
            install_window_chrome(_smoke_app)
            _smoke_window = SmokeWindow()
            if APP_VERSION not in _smoke_window.windowTitle():
                raise RuntimeError("Window version does not match the app version")
            for timer in _smoke_window.findChildren(QTimer):
                timer.stop()
            _smoke_window.show()
            _smoke_app.processEvents()
            _smoke_window.workspace_nav[1].click()
            if _smoke_window.workspace_pages.currentIndex() != 1:
                raise RuntimeError("Account navigation failed")
            _smoke_window.workspace_nav[0].click()
            if not bundled_resource_path("assets/bilibili-tray.png").is_file():
                raise RuntimeError("Missing bundled app icon")
            if _smoke_app.windowIcon().isNull():
                raise RuntimeError("App icon could not be loaded")
            result["checks"].extend(["window", "navigation", "resources"])
            _smoke_window._exit_requested = True
            _smoke_window.close()
            result["ok"] = True
        except Exception as exc:
            result["error"] = str(exc)
        finally:
            if previous_data_dir is None:
                os.environ.pop("BILIDROP_DATA_DIR", None)
            else:
                os.environ["BILIDROP_DATA_DIR"] = previous_data_dir
    # Windowed executables have no stdout. A result path makes CI deterministic.
    if "--smoke-result" in sys.argv:
        index = sys.argv.index("--smoke-result")
        Path(sys.argv[index + 1]).write_text(json.dumps(result, indent=2), encoding="utf-8")
    if sys.stdout is not None:
        print(json.dumps(result))
    return 0 if result["ok"] else 1
