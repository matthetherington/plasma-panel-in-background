#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify and integration-test only the package matching the source metadata."""
import json
from pathlib import Path
import subprocess
import sys


def run(project):
    metadata = json.loads((project / "package/metadata.json").read_text())
    version = metadata["KPlugin"]["Version"]
    archive = project / "dist" / f"plasma-panel-in-background-{version}.plasmoid"
    if not archive.is_file():
        raise FileNotFoundError(f"Build the current package first: {archive}")
    subprocess.run(["sha256sum", "--check", archive.name + ".sha256"],
                   cwd=archive.parent, check=True)
    subprocess.run([sys.executable, str(project / "tests/run-nested.py"),
                    "--input", "--package", str(archive)], check=True)


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])
