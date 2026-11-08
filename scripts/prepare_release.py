#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate a release tag against package metadata and extract its changelog."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def release_notes(tag, metadata, changelog):
    version = metadata["KPlugin"]["Version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", version):
        raise ValueError("Invalid package version")
    if tag != f"v{version}":
        raise ValueError(f"Tag {tag!r} does not match package version v{version}")
    sections = re.split(r"^## ", changelog, flags=re.MULTILINE)
    for section in sections[1:]:
        heading, _, body = section.partition("\n")
        if heading.strip() == version:
            if not body.strip():
                raise ValueError(f"Empty changelog for {version}")
            return body.strip() + "\n"
    raise ValueError(f"Missing changelog section for {version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        notes = release_notes(args.tag,
                              json.loads((ROOT / "package/metadata.json").read_text()),
                              (ROOT / "CHANGELOG.md").read_text())
    except ValueError as error:
        parser.error(str(error))
    args.output.write_text(notes)
