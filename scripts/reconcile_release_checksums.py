"""Keep checksum filenames consistent with names actually stored by GitHub."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def reconcile(metadata: Path, checksums: Path) -> bool:
    release = json.loads(metadata.read_text(encoding="utf-8"))
    entries = []
    for asset in release["assets"]:
        if asset["name"] == "SHA256SUMS.txt":
            continue
        digest = asset.get("digest", "")
        if asset["state"] != "uploaded" or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise ValueError("GitHub must report a SHA-256 digest for every published asset.")
        entries.append(f"{digest.removeprefix('sha256:')}  {asset['name']}")
    if not entries:
        raise ValueError("No published assets to verify.")
    expected = sorted(entries)
    actual = sorted(checksums.read_text(encoding="utf-8").splitlines())
    if actual == expected:
        return False
    checksums.with_suffix(checksums.suffix + ".corrected").write_text("\n".join(expected) + "\n", encoding="utf-8")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--checksums", type=Path, required=True)
    args = parser.parse_args()
    print("Checksum filenames corrected." if reconcile(args.metadata, args.checksums) else "Checksums match published assets.")
