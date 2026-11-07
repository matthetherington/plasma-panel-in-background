# SPDX-License-Identifier: MIT
"""Lifecycle/input assertions for the disposable Plasma session only."""
import json
import os
import subprocess
import time
from input_client import InputClient


def run_extended(root, script, snapshot, restart_plasma):
    device = None
    def config(enabled):
        script('for (var p of panels()) { for (var w of p.widgets("io.github.matthetherington.plasma.panelinbackground")) {'
               'w.currentConfigGroup = ["General"]; w.writeConfig("enabled", '
               + str(enabled).lower() + '); w.reloadConfig(); } }')
        time.sleep(1)

    def panel(label, layer):
        docks = [w for w in snapshot(label) if w["dock"]]
        assert len(docks) == 1 and docks[0]["layer"] == layer, docks
        return docks[0]

    def input_event(action, x, y):
        nonlocal device
        if device is None:
            device = InputClient(root)
        device.event(action, x, y)
        time.sleep(1)

    def edit_mode(enabled):
        subprocess.run(["busctl", "--address=" + os.environ["DBUS_SESSION_BUS_ADDRESS"],
                        "set-property", "org.kde.plasmashell", "/PlasmaShell",
                        "org.kde.PlasmaShell", "editMode", "b", str(enabled).lower()],
                       check=True, timeout=10)
        time.sleep(2)

    def widget_geometry(plugin):
        return json.loads(script('for (var p of panels()) { '
            'for (var w of p.widgets(' + json.dumps(plugin)
            + ')) { print(JSON.stringify(w.geometry)); } }'))

    script('for (var p of panels()) { p.hiding = "autohide"; '
           'p.addWidget("io.github.matthetherington.plasma.panelinbackground"); p.addWidget("org.kde.plasma.kickoff"); }')
    time.sleep(2)
    config(True)
    panel("before-restart", 1)
    restart_plasma()
    panel("after-restart", 1)
    saved = json.loads(script('for (var p of panels()) { '
        'for (var w of p.widgets("io.github.matthetherington.plasma.panelinbackground")) { w.currentConfigGroup=["General"]; '
        'print(JSON.stringify({saved:w.readConfig("savedVisibility")})); } }'))
    assert str(saved["saved"]) == "1", saved
    restart_plasma(hard=True)
    panel("after-hard-restart", 1)
    config(False)
    panel("restart-disabled", 3)
    restored = json.loads(script('for (var p of panels()) { '
        'print(JSON.stringify({hiding:p.hiding})); }'))
    assert restored["hiding"] == "autohide", restored
    assert "PIB restored mode=1 layer=2 zone=-1" in (root / "plasma.log").read_text()
    print("PASS: restart/crash persistence and original auto-hide restoration", flush=True)

    config(True)
    script('for (var p of panels()) { var w=p.addWidget("io.github.matthetherington.plasma.panelinbackground"); '
           'w.currentConfigGroup=["General"]; w.writeConfig("enabled",true); w.reloadConfig(); }')
    time.sleep(2)
    panel("duplicate", 1)
    assert "PIB duplicate controller rejected" in (root / "plasma.log").read_text()
    script('for (var p of panels()) { var ws=p.widgets("io.github.matthetherington.plasma.panelinbackground"); ws[1].remove(); }')
    time.sleep(1)
    panel("duplicate-removed", 1)
    print("PASS: duplicate rejected without changing owning controller", flush=True)

    script('for (var p of panels()) { p.location="left"; }')
    time.sleep(2)
    panel("left-edge", 1)
    script('for (var p of panels()) { p.location="bottom"; }')
    time.sleep(2)
    dock = panel("bottom-edge", 1)
    print("PASS: moving panel between bottom and left edges", flush=True)
    # Move the existing active controller to a different panel/containment.
    script('var old=panels()[0]; var destination=new Panel; '
           'destination.location="left"; destination.hiding="none"; '
           'destination.addWidget(old.widgets("io.github.matthetherington.plasma.panelinbackground")[0]);')
    time.sleep(3)
    moved = [w for w in snapshot("migrated") if w["dock"]]
    assert len(moved) == 2, moved
    assert next(w for w in moved if w["geometry"]["width"] < 100)["layer"] == 1, moved
    assert next(w for w in moved if w["geometry"]["width"] > 100)["layer"] == 3, moved
    config(False)
    saved = json.loads(script('for (var p of panels()) { '
        'for (var w of p.widgets("io.github.matthetherington.plasma.panelinbackground")) { '
        'print(JSON.stringify({hiding:p.hiding})); } }'))
    assert saved["hiding"] == "none", saved
    print("PASS: controller migration restores old panel and adopts new panel state", flush=True)
    if not os.environ.get("PIB_TEST_INPUT"):
        print("SKIP: input/popups; enable with --input", flush=True)
        return
    # Return the controller to a single bottom panel for interaction tests.
    script('var ps=panels(); var source=ps.find(p=>p.widgets("io.github.matthetherington.plasma.panelinbackground").length); '
           'var target=ps.find(p=>p.id!==source.id); '
           'target.addWidget(source.widgets("io.github.matthetherington.plasma.panelinbackground")[0]); source.remove(); '
           'target.hiding="autohide";')
    time.sleep(2)
    config(True)
    dock = panel("input-ready", 1)
    launcher_normal = widget_geometry("org.kde.plasma.kickoff")
    assert launcher_normal["x"] <= 16, launcher_normal
    edit_mode(True)
    geometry = widget_geometry("io.github.matthetherington.plasma.panelinbackground")
    assert 0 < geometry["width"] <= 32 and 0 < geometry["height"] <= 32, geometry
    launcher_editing = widget_geometry("org.kde.plasma.kickoff")
    assert launcher_editing["x"] > launcher_normal["x"], (launcher_editing, launcher_normal)
    print("PASS: hidden without layout space normally; compact control visible in Edit Mode", flush=True)
    dock = panel("input-editing", 1)
    x = dock["geometry"]["x"] + geometry["x"] + geometry["width"] / 2
    y = dock["geometry"]["y"] + geometry["y"] + geometry["height"] / 2
    input_event("move", x, y)
    panel("hover", 1)
    input_event("move", 512, 767)
    panel("screen-edge", 1)
    input_event("rightclick", x, y)
    input_event("home", x, y)
    input_event("enter", x, y)
    clicked = snapshot("click-disabled")
    assert any(w["dock"] and w["layer"] == 3 for w in clicked), clicked
    # The disabled controller must remain accessible in Edit Mode too.
    disabled_geometry = widget_geometry("io.github.matthetherington.plasma.panelinbackground")
    assert disabled_geometry["width"] > 0 and disabled_geometry["height"] > 0, disabled_geometry
    input_event("rightclick", x, y)
    input_event("home", x, y)
    input_event("enter", x, y)
    panel("context-reenabled", 1)
    edit_mode(False)
    dock = panel("input-enabled", 1)
    kickoff = json.loads(script('for (var p of panels()) { '
        'for (var w of p.widgets("org.kde.plasma.kickoff")) { print(JSON.stringify(w.geometry)); } }'))
    input_event("click", dock["geometry"]["x"] + kickoff["x"] + kickoff["width"] / 2,
                dock["geometry"]["y"] + kickoff["y"] + kickoff["height"] / 2)
    windows = snapshot("launcher-open")
    docks = [w for w in windows if w["dock"]]
    assert len(docks) == 1 and docks[0]["layer"] == 1, windows
    assert any(not w["dock"] and w["layer"] > 2
               and not w["tooltip"] and w["geometry"]["height"] > 200
               and w["caption"] != "Welcome Center" for w in windows), windows
    input_event("escape", 512, 384)
    closed = snapshot("launcher-closed")
    assert next(w for w in closed if w["dock"])["layer"] == 1, closed
    assert not any(w["caption"] == "plasmashell" and not w["tooltip"]
                   and not w["hidden"] and w["geometry"]["height"] > 200
                   for w in closed), closed
    print("PASS: Edit Mode context-menu toggles, hover/edge stability, launcher open/Escape close", flush=True)
    # Exercise the native edit-mode exception without changing the panel's layer.
    for enabled in (True, False):
        edit_mode(enabled)
        edited = snapshot("edit-" + str(enabled).lower())
        dock = next(w for w in edited if w["dock"])
        assert dock["layer"] == 1 and not dock["hidden"], edited
    print("PASS: entering/leaving Plasma edit mode preserves panel layer", flush=True)
    device.close()
