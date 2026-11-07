#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Disposable headless Plasma session. Does not install into the user's desktop."""
from pathlib import Path
import argparse
import os
import signal
import subprocess
import tempfile

project = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--input", action="store_true", help="Also run synthetic-input/popup tests")
parser.add_argument("--visible", action="store_true", help="Show the disposable compositor in a window")
parser.add_argument("--diagnose", action="store_true", help="Run short rendering/input diagnostics instead of full suite")
parser.add_argument("--package", type=Path, help="Install/test a built .plasmoid instead of symlinking source")
args = parser.parse_args()
root = Path(tempfile.mkdtemp(prefix="panel-in-background-nested-", dir="/tmp/opencode"))
for name in ("config", "data", "state", "cache", "runtime"):
    (root / name).mkdir(mode=0o700)
widgets = root / "data/plasma/plasmoids"
widgets.mkdir(parents=True)
if not args.package:
    (widgets / "io.github.matthetherington.plasma.panelinbackground").symlink_to(project / "package", target_is_directory=True)
env = dict(os.environ)
env.pop("PIB_TEST_PACKAGE", None)
if args.package:
    archive = args.package.resolve()
    if not archive.is_file():
        parser.error("--package must name an existing .plasmoid archive")
    env["PIB_TEST_PACKAGE"] = str(archive)
env.pop("PIB_PARENT_DISPLAY", None)
env.pop("PIB_DIAGNOSE", None)
if args.visible:
    parent_display = os.environ.get("WAYLAND_DISPLAY", "")
    if not parent_display:
        parser.error("--visible requires a parent Wayland session")
    env["PIB_PARENT_DISPLAY"] = str(Path(os.environ["XDG_RUNTIME_DIR"]) / parent_display)
if args.diagnose:
    env["PIB_DIAGNOSE"] = "1"
for key, value in (("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                   ("XDG_STATE_HOME", "state"), ("XDG_CACHE_HOME", "cache"),
                   ("XDG_RUNTIME_DIR", "runtime")):
    env[key] = str(root / value)
env.update(PIB_TEST_ROOT=str(root), QT_QPA_PLATFORM="wayland",
           QT_FORCE_STDERR_LOGGING="1", QT_LOGGING_RULES="*.debug=false;qml.debug=true;kwin_scripting.debug=true;js.debug=true",
           WAYLAND_DISPLAY="panel-in-background-test", LIBGL_ALWAYS_SOFTWARE="1")
for key in ("SESSION_MANAGER", "DBUS_SESSION_BUS_ADDRESS", "DISPLAY",
            "QT_WAYLAND_SHELL_INTEGRATION"):
    env.pop(key, None)
print("Test directory:", root, flush=True)
if args.input or args.diagnose:
    env["PIB_TEST_INPUT"] = "1"
    subprocess.run(["cc", "-Wall", "-Wextra", str(project / "tests/nested-input.c"),
                    "-lwayland-client", "-lm", "-o", str(root / "nested-input")], check=True)
else:
    env.pop("PIB_TEST_INPUT", None)
process = subprocess.Popen(
    ["dbus-run-session", "--", "python3", str(project / "tests/nested-session.py")],
    env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    start_new_session=True,
)
try:
    stdout, stderr = process.communicate(timeout=180)
except (subprocess.TimeoutExpired, KeyboardInterrupt):
    # The process group contains only this disposable session and its children.
    os.killpg(process.pid, signal.SIGTERM)
    try:
        stdout, stderr = process.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    (root / "driver.log").write_text(stdout + stderr)
    raise
(root / "driver.log").write_text(stdout + stderr)
print(stdout)
for name in ("kwin.log", "plasma.log"):
    if (root / name).exists():
        lines = (root / name).read_text().splitlines()
        print(name + ":")
        print("\n".join(line for line in lines if any(
            token in line for token in ("PIB", "Error", "error", "failed", "unavailable", "Aborting")
        ))[-6000:])
if process.returncode:
    print(stderr[-4000:])
raise SystemExit(process.returncode)
