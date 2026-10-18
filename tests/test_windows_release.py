import hashlib
import json

import pytest

from bilibili_drops_miner._version import APP_VERSION
from scripts.prepare_windows_release import prepare
from scripts.reconcile_release_checksums import reconcile


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
    assert (tmp_path / "release/Windows.md").is_file()
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


def test_checksums_follow_github_asset_names_without_changing_the_digest(tmp_path):
    metadata = tmp_path / "release.json"
    digest = "a" * 64
    metadata.write_text(json.dumps({"assets": [{"name": "Windows.md", "state": "uploaded", "digest": f"sha256:{digest}"}]}))
    checksums = tmp_path / "SHA256SUMS.txt"
    checksums.write_text(f"{digest}  Windows使用说明.md\n", encoding="utf-8")
    assert reconcile(metadata, checksums)
    corrected = checksums.with_suffix(".txt.corrected").read_text(encoding="utf-8")
    assert corrected == f"{digest}  Windows.md\n"
    checksums.write_text(corrected, encoding="utf-8")
    assert not reconcile(metadata, checksums)


def test_checksums_cannot_be_repaired_without_a_github_digest(tmp_path):
    metadata = tmp_path / "release.json"
    metadata.write_text(json.dumps({"assets": [{"name": "Windows.md", "state": "uploaded"}]}))
    checksums = tmp_path / "SHA256SUMS.txt"
    checksums.write_text("unchanged\n", encoding="utf-8")
    with pytest.raises(ValueError):
        reconcile(metadata, checksums)
    assert not checksums.with_suffix(".txt.corrected").exists()
