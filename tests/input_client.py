# SPDX-License-Identifier: MIT
"""Keep one input device alive so clients don't repeatedly lose wl_seat capabilities."""
import atexit
import os
import select
import subprocess


class InputClient:
    def __init__(self, root):
        env = dict(os.environ)
        if os.environ.get("PIB_WIRE"):
            env["WAYLAND_DEBUG"] = "client"
        self.process = subprocess.Popen([str(root / "nested-input"), "serve", "0", "0"],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env)
        atexit.register(self.close)
        self._expect("READY")

    def _expect(self, message):
        assert select.select([self.process.stdout], [], [], 10)[0], "Input helper timeout"
        reply = self.process.stdout.readline().strip()
        assert reply == message, reply

    def event(self, action, x, y):
        self.process.stdin.write(f"{action} {x} {y}\n")
        self.process.stdin.flush()
        self._expect("DONE")

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=3)
