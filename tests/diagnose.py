# SPDX-License-Identifier: MIT
"""Short input/rendering comparison, restricted to the disposable session."""
import json
import os
import subprocess
import time
from input_client import InputClient


def run_diagnostics(root, script, snapshot):
    device = InputClient(root)
    script('for (var old of panels()) { old.remove(); } '
           'var p=new Panel; p.location="bottom"; p.hiding="none"; '
           'p.addWidget("io.github.matthetherington.plasma.panelinbackground"); p.addWidget("org.kde.plasma.kickoff");')
    time.sleep(3)

    def input_event(action, x, y):
        device.event(action, x, y)
        time.sleep(1)

    def screenshot(label):
        with (root / "spectacle.log").open("a") as log:
            try:
                subprocess.run(["spectacle", "--background", "--nonotify", "--fullscreen",
                                "--output", str(root / (label + ".png"))],
                               stdout=log, stderr=log, timeout=15)
            except subprocess.TimeoutExpired:
                print("Screenshot timed out:", label, flush=True)

    def centre(plugin):
        dock = next(w for w in snapshot("locate-" + plugin) if w["dock"])
        rect = json.loads(script('for (var p of panels()) { for (var w of p.widgets('
            + json.dumps(plugin) + ')) { print(JSON.stringify(w.geometry)); } }'))
        return (dock["geometry"]["x"] + rect["x"] + rect["width"] / 2,
                dock["geometry"]["y"] + rect["y"] + rect["height"] / 2)

    screenshot("normal")
    subprocess.run(["busctl", "--address=" + os.environ["DBUS_SESSION_BUS_ADDRESS"],
                    "set-property", "org.kde.plasmashell", "/PlasmaShell",
                    "org.kde.PlasmaShell", "editMode", "b", "true"], check=True)
    time.sleep(2)
    screenshot("editing")
    input_event("rightclick", *centre("io.github.matthetherington.plasma.panelinbackground"))
    screenshot("context-menu")
    input_event("home", *centre("io.github.matthetherington.plasma.panelinbackground"))
    input_event("enter", *centre("io.github.matthetherington.plasma.panelinbackground"))
    snapshot("toggle-click")
    screenshot("after-toggle")
    subprocess.run(["busctl", "--address=" + os.environ["DBUS_SESSION_BUS_ADDRESS"],
                    "set-property", "org.kde.plasmashell", "/PlasmaShell",
                    "org.kde.PlasmaShell", "editMode", "b", "false"], check=True)
    time.sleep(2)
    input_event("click", *centre("org.kde.plasma.kickoff"))
    snapshot("stock-launcher-click")
    screenshot("after-launcher")
    input_event("escape", 512, 384)
    print("Diagnostics complete; screenshots/logs in", root, flush=True)
    device.close()
