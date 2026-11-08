# SPDX-License-Identifier: MIT
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_ci", ROOT / "tests/run-ci.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class CIRunnerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.project = Path(directory.name)
        (self.project / "package").mkdir()
        (self.project / "dist").mkdir()
        (self.project / "package/metadata.json").write_text(
            json.dumps({"KPlugin": {"Version": "1.2.3"}}))
        self.archive = self.project / "dist/plasma-panel-in-background-1.2.3.plasmoid"

    @patch.object(runner.subprocess, "run")
    def test_selects_current_version_not_stale_packages(self, execute):
        self.archive.touch()
        (self.archive.parent / "plasma-panel-in-background-1.2.2.plasmoid").touch()
        runner.run(self.project)
        self.assertEqual(execute.call_count, 2)
        self.assertEqual(execute.call_args_list[0].args[0],
                         ["sha256sum", "--check", self.archive.name + ".sha256"])
        self.assertEqual(execute.call_args_list[0].kwargs,
                         {"cwd": self.archive.parent, "check": True})
        execute.assert_called_with(
            [sys.executable, str(self.project / "tests/run-nested.py"),
             "--input", "--package", str(self.archive)], check=True)

    @patch.object(runner.subprocess, "run")
    def test_missing_current_package_does_not_use_an_old_one(self, execute):
        (self.archive.parent / "plasma-panel-in-background-1.2.2.plasmoid").touch()
        with self.assertRaises(FileNotFoundError):
            runner.run(self.project)
        execute.assert_not_called()

    @patch.object(runner.subprocess, "run")
    def test_checksum_failure_blocks_integration_tests(self, execute):
        self.archive.touch()
        execute.side_effect = subprocess.CalledProcessError(1, "sha256sum")
        with self.assertRaises(subprocess.CalledProcessError):
            runner.run(self.project)
        self.assertEqual(execute.call_count, 1)


if __name__ == "__main__":
    unittest.main()
