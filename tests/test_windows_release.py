import hashlib
import json

import pytest

from bilibili_drops_miner._version import APP_VERSION
from scripts.prepare_windows_release import prepare


def make_artifact(tmp_path, **smoke_changes):
    artifact = tmp_path / "artifact"
    (artifact / "dist").mkdir(parents=True)
    (artifact / "docs").mkdir()
    (artifact / "dist/bilibili-drops-miner-gui.exe").write_bytes(b"MZtest-executable")
    (artifact / "docs/windows.md").write_text("Windows guide", encoding="utf-8")
    (artifact / "LICENSE").write_text("MIT", encoding="utf-8")
    smoke = {
        "ok": True,
        "version": APP_VERSION,
        "checks": ["timezone", "dpapi", "window", "navigation", "resources"],
        **smoke_changes,
    }
    (artifact / "dist/windows-smoke-result.json").write_text(json.dumps(smoke), encoding="utf-8")
    return artifact


def test_release_assets_keep_the_validated_executable_and_match_checksums(tmp_path):
    artifact = make_artifact(tmp_path)
    assets = prepare(artifact, tmp_path / "release")
    executable = assets[0]
    assert executable.name == f"BiliCompanion-{APP_VERSION}-Windows-x64.exe"
    assert executable.read_bytes() == (artifact / "dist/bilibili-drops-miner-gui.exe").read_bytes()
    checksums = (tmp_path / "release/SHA256SUMS.txt").read_text(encoding="utf-8")
    for asset in assets[:-1]:
        assert f"{hashlib.sha256(asset.read_bytes()).hexdigest()}  {asset.name}\n" in checksums


@pytest.mark.parametrize("changes", [{"ok": False}, {"version": "v0.0.0"}, {"checks": ["window"]}])
def test_release_rejects_failed_mismatched_or_incomplete_smoke_test(tmp_path, changes):
    artifact = make_artifact(tmp_path, **changes)
    with pytest.raises(ValueError):
        prepare(artifact, tmp_path / "release")
    assert not (tmp_path / "release").exists()
