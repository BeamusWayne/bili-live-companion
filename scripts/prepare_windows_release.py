"""Package the validated Windows artifact for a GitHub Release."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
import shutil
from pathlib import Path


def prepare(artifact: Path, output: Path) -> list[Path]:
    root = Path(__file__).resolve().parents[1]
    version = runpy.run_path(str(root / "bilibili_drops_miner/_version.py"))["APP_VERSION"]
    smoke_path = artifact / "dist/windows-smoke-result.json"
    smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
    required_checks = {"timezone", "dpapi", "window", "navigation", "resources"}
    if not smoke.get("ok") or smoke.get("version") != version:
        raise ValueError("The executable must pass its smoke test with the release version.")
    if not required_checks.issubset(smoke.get("checks", [])):
        raise ValueError("The executable smoke test is missing required checks.")
    binary = artifact / "dist/bilibili-drops-miner-gui.exe"
    with binary.open("rb") as handle:
        if handle.read(2) != b"MZ":
            raise ValueError("The artifact is not a Windows executable.")
    output.mkdir(parents=True, exist_ok=False)
    sources = {
        f"BiliCompanion-{version}-Windows-x64.exe": binary,
        "Windows.md": artifact / "docs/windows.md",
        "LICENSE.txt": artifact / "LICENSE",
        "windows-smoke-result.json": smoke_path,
    }
    assets = []
    for name, source in sources.items():
        destination = output / name
        shutil.copyfile(source, destination)
        assets.append(destination)
    checksum = output / "SHA256SUMS.txt"
    checksum.write_text(
        "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in assets),
        encoding="utf-8",
    )
    return [*assets, checksum]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for asset in prepare(args.artifact, args.output):
        print(asset.name)
