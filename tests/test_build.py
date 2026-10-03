import sys

import build as build_module


def test_macos_gui_build_uses_app_bundle_and_png_icon(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(build_module.sys, "platform", "darwin")
    monkeypatch.setattr(sys, "argv", ["build.py", "--target", "gui"])
    monkeypatch.setattr(build_module, "ensure_pyinstaller", lambda: None)
    monkeypatch.setattr(build_module, "build", lambda *args, **kwargs: calls.append((args, kwargs)))

    build_module.main()

    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[:2] == ("bilibili_gui.py", "bilibili-drops-miner-gui")
    assert kwargs["windowed"] is True
    assert kwargs["onefile"] is False
    extra = kwargs["extra_args"]
    assert extra[extra.index("--icon") + 1] == "assets/bilibili.png"
    assert extra[extra.index("--osx-bundle-identifier") + 1] == "com.bilidrop.desktop"
