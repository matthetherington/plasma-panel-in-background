#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run only inside a private dbus-run-session, with disposable XDG directories."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(os.environ["PIB_TEST_ROOT"])
project = Path(__file__).resolve().parents[1]
assert str(root).startswith("/tmp/opencode/")
assert os.environ["XDG_CONFIG_HOME"] == str(root / "config")


def script(source):
    result = subprocess.run(
        ["qdbus-qt6", "org.kde.plasmashell", "/PlasmaShell",
         "org.kde.PlasmaShell.evaluateScript", source],
        capture_output=True, text=True, timeout=10, check=True,
    )
    print(result.stdout.strip(), flush=True)
    return result.stdout


def wait_for(test, seconds=25):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if test():
            return
        time.sleep(0.3)
    raise RuntimeError("Readiness timeout")


kwin = None
plasma = None
activities = None
cover = None
snapshot_number = 0


def snapshot(label):
    global snapshot_number
    snapshot_number += 1
    path = root / f"snapshot-{snapshot_number}.js"
    path.write_text('print("PIB_CURSOR ' + label + ' " + JSON.stringify(workspace.cursorPos)); '
                    'for (var w of workspace.windowList()) { '
                    'print("PIB_SNAPSHOT ' + label + ' " + JSON.stringify({'
                    'caption:w.caption, dock:w.dock, layer:w.layer, hidden:w.hidden, tooltip:w.tooltip, '
                    'geometry:w.frameGeometry, stackingOrder:w.stackingOrder})); }')
    loaded = subprocess.run(["qdbus-qt6", "org.kde.KWin", "/Scripting",
                    "org.kde.kwin.Scripting.loadScript", str(path),
                    f"panel-in-background-snapshot-{snapshot_number}"], check=True,
                   capture_output=True, text=True, timeout=10)
    subprocess.run(["qdbus-qt6", "org.kde.KWin", "/Scripting/Script" + loaded.stdout.strip(),
                    "org.kde.kwin.Script.run"], check=True,
                   capture_output=True, text=True, timeout=10)
    time.sleep(0.5)
    result = []
    for line in (root / "kwin.log").read_text().splitlines():
        marker = "PIB_SNAPSHOT " + label + " "
        if marker in line:
            result.append(json.loads(line.split(marker, 1)[1]))
    assert result, "No compositor observations for " + label
    return result
try:
    with (root / "kwin.log").open("w") as log:
        kwin = subprocess.Popen(
            ["kwin_wayland"] + (["--wayland-display", os.environ["PIB_PARENT_DISPLAY"]]
                if os.environ.get("PIB_PARENT_DISPLAY") else ["--virtual"]) + ["--width", "1024", "--height", "768",
             "--socket", "panel-in-background-test", "--no-lockscreen", "--no-global-shortcuts",
             "--no-kactivities"], stdout=log, stderr=subprocess.STDOUT,
        )
    wait_for(lambda: (Path(os.environ["XDG_RUNTIME_DIR"]) / "panel-in-background-test").exists())
    os.environ["WAYLAND_DISPLAY"] = "panel-in-background-test"
    if os.environ.get("PIB_TEST_PACKAGE"):
        subprocess.run(["kpackagetool6", "--type", "Plasma/Applet", "--packageroot",
                        str(root / "data/plasma/plasmoids"), "--install",
                        os.environ["PIB_TEST_PACKAGE"]], check=True, timeout=20)
    with (root / "activities.log").open("w") as log:
        activities = subprocess.Popen(["/usr/libexec/kactivitymanagerd"], stdout=log,
                                      stderr=subprocess.STDOUT)
    wait_for(lambda: subprocess.run(
        ["qdbus-qt6", "org.kde.ActivityManager", "/ActivityManager"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0)
    with (root / "plasma.log").open("w") as log:
        plasma_env = dict(os.environ)
        if os.environ.get("PIB_WIRE"):
            plasma_env["WAYLAND_DEBUG"] = "client"
        if os.environ.get("PIB_QT_INPUT"):
            plasma_env["QT_LOGGING_RULES"] += ";qt.quick.pointer.*=true;qt.quick.mouse.*=true"
        plasma = subprocess.Popen(["plasmashell", "--no-respawn"], stdout=log,
                                  stderr=subprocess.STDOUT, env=plasma_env)

    def plasma_ready():
        return subprocess.run(
            ["qdbus-qt6", "org.kde.plasmashell", "/PlasmaShell"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode == 0

    wait_for(plasma_ready)
    time.sleep(3)
    if os.environ.get("PIB_DIAGNOSE"):
        from diagnose import run_diagnostics
        run_diagnostics(root, script, snapshot)
        sys.exit(0)
    script('for (var old of panels()) { old.remove(); } '
           'var p = new Panel; p.location = "bottom"; p.hiding = "autohide"; '
           'var w = p.addWidget("io.github.matthetherington.plasma.panelinbackground"); '
           'print(JSON.stringify({panel:p.id, widget:w.id}));')
    time.sleep(3)
    script('var ps = panels(); for (var p of ps) { for (var w of p.widgets()) {'
           'if (w.type === "io.github.matthetherington.plasma.panelinbackground") { w.currentConfigGroup = ["General"]; '
           'w.writeConfig("enabled", true); w.reloadConfig(); } } }')
    time.sleep(3)
    snapshot("enabled")
    with (root / "cover.log").open("w") as log:
        cover = subprocess.Popen(["/usr/lib64/qt6/bin/qml", str(project / "tests/cover-window.qml")],
                                 stdout=log, stderr=subprocess.STDOUT)
    time.sleep(2)
    snapshot("partial")
    time.sleep(4)
    snapshot("maximised")
    script('var ps = panels(); for (var p of ps) { for (var w of p.widgets()) {'
           'if (w.type === "io.github.matthetherington.plasma.panelinbackground") { w.currentConfigGroup = ["General"]; '
           'print(JSON.stringify({panel:p.id,saved:w.readConfig("savedVisibility")})); '
           'w.writeConfig("enabled", false); w.reloadConfig(); } } }')
    time.sleep(3)
    snapshot("disabled")
    log = (root / "plasma.log").read_text()
    assert "PIB enabled mode=3 layer=1 zone=-1" in log, log
    assert "PIB restored mode=1 layer=2 zone=-1" in log, log
    observations = []
    for line in (root / "kwin.log").read_text().splitlines():
        if "PIB_SNAPSHOT " in line:
            label, data = line.split("PIB_SNAPSHOT ", 1)[1].split(" ", 1)
            observations.append((label, json.loads(data)))
    for label in ("partial", "maximised"):
        windows = [w for phase, w in observations if phase == label]
        panel = next(w for w in windows if w["dock"])
        app = next(w for w in windows if w["caption"] == "Panel in Background cover test")
        assert panel["layer"] == 1 and app["layer"] == 2, windows
        assert panel["stackingOrder"] < app["stackingOrder"], windows
        a, b = app["geometry"], panel["geometry"]
        assert a["y"] + a["height"] > b["y"], windows
        if label == "maximised":
            assert a == {"x": 0, "y": 0, "width": 1024, "height": 768}, a
    # A deliberate native visibility choice must win over the controller.
    script('for (var p of panels()) { for (var w of p.widgets()) {'
           'if (w.type === "io.github.matthetherington.plasma.panelinbackground") { w.currentConfigGroup = ["General"]; '
           'w.writeConfig("enabled", true); w.reloadConfig(); } } }')
    time.sleep(2)
    script('for (var p of panels()) { p.hiding = "none"; }')
    time.sleep(2)
    state = script('for (var p of panels()) { for (var w of p.widgets()) {'
                   'if (w.type === "io.github.matthetherington.plasma.panelinbackground") { w.currentConfigGroup = ["General"]; '
                   'print(JSON.stringify({enabled:w.readConfig("enabled")})); } } }')
    assert json.loads(state)["enabled"] in (False, "", "false"), state
    # Removing an enabled widget must restore the original normal visibility mode.
    script('for (var p of panels()) { for (var w of p.widgets()) {'
           'if (w.type === "io.github.matthetherington.plasma.panelinbackground") { w.currentConfigGroup = ["General"]; '
           'w.writeConfig("enabled", true); w.reloadConfig(); } } }')
    time.sleep(2)
    script('for (var p of panels()) { for (var w of p.widgets()) {'
           'if (w.type === "io.github.matthetherington.plasma.panelinbackground") { w.remove(); } } }')
    time.sleep(3)
    snapshot("removed")
    log = (root / "plasma.log").read_text()
    assert log.count("PIB restored mode=0 layer=2") >= 2, log
    print("PASS: compositor stacking, overlap, full-screen maximisation, disable, native choice, removal", flush=True)
    from extended import run_extended

    def restart_plasma(hard=False):
        global plasma
        if hard:
            plasma.kill()
        else:
            plasma.terminate()
        plasma.wait(timeout=10)
        wait_for(lambda: not plasma_ready())
        with (root / "plasma.log").open("a") as log:
            plasma = subprocess.Popen(["plasmashell", "--no-respawn"], stdout=log,
                                      stderr=subprocess.STDOUT)
        wait_for(plasma_ready)
        time.sleep(4)

    # Keep test windows from obscuring controls during synthetic-input checks.
    cover.terminate()
    cover.wait(timeout=5)
    cover = None
    run_extended(root, script, snapshot, restart_plasma)
finally:
    for process in (cover, plasma, activities, kwin):
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
