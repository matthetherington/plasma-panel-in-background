#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read live panel layer/geometry via a temporary, read-only KWin script."""
import json
import os
from pathlib import Path
import tempfile

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
loop = GLib.MainLoop()
service = "io.github.matthetherington.plasma.panelinbackground.Observer.p" + str(os.getpid())
name = dbus.service.BusName(service, bus=bus, do_not_queue=True)
observations = []


class Observer(dbus.service.Object):
    @dbus.service.method("io.github.matthetherington.plasma.panelinbackground.Observer", in_signature="s", out_signature="")
    def Submit(self, value):
        observations.extend(json.loads(str(value)))
        loop.quit()


observer = Observer(bus, "/Observer")
scripting = dbus.Interface(bus.get_object("org.kde.KWin", "/Scripting"), "org.kde.kwin.Scripting")
plugin = "panel-in-background-observe-" + str(os.getpid())
test_directory = Path("/tmp/panel-in-background-tests")
test_directory.mkdir(mode=0o700, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="panel-in-background-observer-", dir=test_directory) as temporary:
    source = Path(temporary) / "observe.js"
    source.write_text('var result=[]; for (var w of workspace.windowList()) { '
        'if (w.dock && w.resourceClass === "plasmashell") { '
        'result.push({layer:w.layer,hidden:w.hidden,geometry:w.frameGeometry}); } } '
        'callDBus(' + json.dumps(service) + ',"/Observer","io.github.matthetherington.plasma.panelinbackground.Observer",'
        '"Submit",JSON.stringify(result));')
    # loadScript is overloaded; python-dbus introspection may select its one-arg form.
    script_id = bus.call_blocking("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting",
                                  "loadScript", "ss", (str(source), plugin))
    if script_id < 0:
        raise RuntimeError("Could not load temporary observation script")
    try:
        runtime = dbus.Interface(bus.get_object("org.kde.KWin", "/Scripting/Script" + str(script_id)),
                                 "org.kde.kwin.Script")
        runtime.run()
        GLib.timeout_add_seconds(8, lambda: (loop.quit(), False)[1])
        loop.run()
        if not observations:
            raise RuntimeError("No panel observations received")
        print(json.dumps(observations, indent=2))
    finally:
        scripting.unloadScript(plugin)
