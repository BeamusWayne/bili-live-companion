from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from bilibili_drops_miner._version import APP_VERSION


PYINSTALLER_REQUIREMENT = "PyInstaller==6.20.0"


def build_environment() -> dict[str, str]:
    env = os.environ.copy()
    if sys.platform == "win32":
        # Unrelated toolchains on PATH can supply incompatible ICU/OpenSSL DLLs.
        # Resolve dependencies from this Python and the Windows system instead.
        python_root = Path(sys.base_prefix)
        windows_root = Path(env.get("SystemRoot", r"C:\Windows"))
        env["PATH"] = os.pathsep.join(str(path) for path in (
            python_root, python_root / "DLLs", windows_root / "System32", windows_root,
        ))
    return env


def write_windows_version_info() -> Path:
    """Embed the same version shown in Qt into Windows executable properties."""
    numbers = [int(part) for part in re.findall(r"\d+", APP_VERSION)]
    version = tuple((numbers + [0, 0, 0, 0])[:4])
    if any(part > 65535 for part in version):
        raise ValueError("Windows version components must fit in 16 bits")
    display_version = APP_VERSION.lstrip("v")
    flags = 2 if "-" in display_version else 0
    text = f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers={version!r}, prodvers={version!r}, mask=0x3f,
    flags={flags}, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('FileDescription', 'Bili Live Companion'),
    StringStruct('ProductName', 'Bili Live Companion'),
    StringStruct('FileVersion', {'.'.join(map(str, version))!r}),
    StringStruct('ProductVersion', {display_version!r})
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)'''
    path = Path("build/windows-version-info.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller not found, installing...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", PYINSTALLER_REQUIREMENT]
        )


def format_cmd(cmd: list[str]) -> str:
    if sys.platform == "win32":
        return subprocess.list2cmdline(cmd)
    return shlex.join(cmd)


def build(
    entry: str,
    name: str,
    *,
    windowed: bool = False,
    onefile: bool = False,
    clean: bool = False,
    noupx: bool = True,
    debug: bool = False,
    extra_args: Iterable[str] | None = None,
) -> None:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--name",
        name,
    ]

    cmd.append("--onefile" if onefile else "--onedir")

    if clean:
        cmd.append("--clean")

    if noupx:
        cmd.append("--noupx")

    if windowed:
        cmd.append("--windowed")

    if debug:
        cmd.extend(["--log-level", "DEBUG"])

    if extra_args:
        cmd.extend(extra_args)

    cmd.append(entry)

    print(f"\nBuilding {name} ...")
    print(format_cmd(cmd))
    subprocess.check_call(cmd, env=build_environment())

    if windowed and sys.platform == "darwin":
        print(f"Done: dist/{name}.app")
    elif onefile:
        extension = ".exe" if sys.platform == "win32" else ""
        print(f"Done: dist/{name}{extension}")
    else:
        print(f"Done: dist/{name}/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Bilibili Drops Miner with PyInstaller."
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="compatibility flag; builds the platform's default output.",
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="build an unpacked directory (default for macOS apps).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="clean PyInstaller cache before build.",
    )
    parser.add_argument(
        "--target",
        choices=["gui", "cli", "all"],
        default="all",
        help="select which target to build.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable PyInstaller debug log output.",
    )
    parser.add_argument(
        "--name-suffix",
        default="",
        help="append a suffix to output names so a running build is not overwritten.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_pyinstaller()

    onefile = not args.onedir and sys.platform != "darwin"
    suffix = args.name_suffix.strip().strip("-")
    if suffix and any(char in suffix for char in "\\/:*?\"<>|"):
        raise ValueError("--name-suffix 包含 Windows 文件名不支持的字符")
    gui_name = "bilibili-drops-miner-gui"
    cli_name = "bilibili-drops-miner-cli"
    if suffix:
        gui_name = f"{gui_name}-{suffix}"
        cli_name = f"{cli_name}-{suffix}"

    # 发布包使用 notifier.py 里的轻量内置通知，避免把 Apprise 的全量插件
    # 都塞进包里。源码环境仍可通过 Apprise 回退支持更多通知渠道。
    unused_optional_excludes = [
        "--exclude-module",
        "IPython",
        "--exclude-module",
        "jedi",
        "--exclude-module",
        "jinja2",
        "--exclude-module",
        "matplotlib",
        "--exclude-module",
        "numpy",
        "--exclude-module",
        "PIL",
        "--exclude-module",
        "prompt_toolkit",
        "--exclude-module",
        "pygments",
        "--exclude-module",
        "tkinter",
        "--exclude-module",
        "traitlets",
        "--exclude-module",
        "pytest",
        "--exclude-module",
        "_pytest",
    ]
    common_extra_args = unused_optional_excludes + ["--exclude-module", "apprise"]

    icon_png = Path("assets/bilibili-tray.png")
    icon_ico = Path("assets/bilibili-tray.ico")
    tray_icon_ico = Path("assets/bilibili-tray.ico")
    gui_extra_args = common_extra_args + [
        "--icon",
        (icon_png if sys.platform == "darwin" else icon_ico).as_posix(),
        "--add-data",
        f"{icon_png}{os.pathsep}assets",
        "--add-data",
        f"{tray_icon_ico}{os.pathsep}assets",
        # Selenium 4 lazy-loads browser classes. Include the two supported
        # browsers and their manager binaries in the packaged application.
        "--hidden-import",
        "selenium.webdriver.chrome.webdriver",
        "--hidden-import",
        "selenium.webdriver.chrome.options",
        "--hidden-import",
        "selenium.webdriver.chrome.service",
        "--hidden-import",
        "selenium.webdriver.edge.webdriver",
        "--hidden-import",
        "selenium.webdriver.edge.options",
        "--hidden-import",
        "selenium.webdriver.edge.service",
        "--collect-data",
        "tzdata",
    ]
    if sys.platform == "darwin":
        gui_extra_args.extend(
            ["--osx-bundle-identifier", "com.bilidrop.desktop"]
        )
    elif sys.platform == "win32":
        gui_extra_args.extend(["--version-file", str(write_windows_version_info())])

    if args.target in ("gui", "all"):
        build(
            "bilibili_gui.py",
            gui_name,
            windowed=True,
            onefile=onefile,
            clean=args.clean,
            noupx=True,
            debug=args.debug,
            extra_args=gui_extra_args,
        )

    if args.target in ("cli", "all"):
        build(
            "bilibili.py",
            cli_name,
            onefile=onefile,
            clean=False,  # 避免第二个目标再次清缓存
            noupx=True,
            debug=args.debug,
            extra_args=common_extra_args,
        )

    mode = "single-file" if onefile else "development-directory"
    print(f"\nAll builds complete. Mode: {mode}. Output in dist/")


if __name__ == "__main__":
    main()
