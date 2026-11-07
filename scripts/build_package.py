#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a reproducible, architecture-independent Plasma applet archive."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    "LICENSE", "README.md", "CHANGELOG.md",
    "docs/COMPATIBILITY.md", "docs/TROUBLESHOOTING.md", "docs/DEVELOPMENT.md",
    "docs/images/panel-in-background.png",
)


def build(output_directory):
    package = ROOT / "package"
    metadata = json.loads((package / "metadata.json").read_text())
    plugin = metadata["KPlugin"]
    version = plugin["Version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", version):
        raise ValueError("Invalid package version")
    if plugin["Id"] != "io.github.matthetherington.plasma.panelinbackground" or plugin["License"] != "MIT":
        raise ValueError("Unexpected package identity or licence")

    members = {}
    for source in sorted(package.rglob("*")):
        if source.is_symlink():
            raise ValueError(f"Refusing package symlink: {source}")
        if source.is_file():
            relative = source.relative_to(package).as_posix()
            if relative != "metadata.json" and not (
                relative.startswith("contents/") and source.suffix in (".qml", ".js", ".xml")
            ):
                raise ValueError(f"Unexpected package file: {relative}")
            members[relative] = source
    for relative in PUBLIC_FILES:
        members[relative] = ROOT / relative
    for required in ("metadata.json", "contents/ui/main.qml", "contents/config/main.xml"):
        if required not in members:
            raise ValueError(f"Missing package entry: {required}")

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"plasma-panel-in-background-{version}.plasmoid"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package_zip:
        for relative, source in sorted(members.items()):
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            package_zip.writestr(info, source.read_bytes(), compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    result = build(args.output_dir)
    print(result)
    print(result.with_suffix(result.suffix + ".sha256"))
