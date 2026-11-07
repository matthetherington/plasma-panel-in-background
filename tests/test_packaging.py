# SPDX-License-Identifier: MIT
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_package", ROOT / "scripts/build_package.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.archive = builder.build(self.directory.name)

    def test_layout_and_public_files_only(self):
        with zipfile.ZipFile(self.archive) as archive:
            expected = {
                "metadata.json", "contents/ui/main.qml", "contents/ui/owners.js",
                "contents/config/main.xml", *builder.PUBLIC_FILES,
            }
            self.assertEqual(set(archive.namelist()), expected)
            self.assertIsNone(archive.testzip())
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.external_attr >> 16, 0o100644)
                if not info.filename.endswith(".png"):
                    self.assertNotIn("/home/", archive.read(info).decode())
            metadata = json.loads(archive.read("metadata.json"))
            self.assertEqual(metadata["KPackageStructure"], "Plasma/Applet")
            self.assertEqual(metadata["KPlugin"]["Id"], "io.github.matthetherington.plasma.panelinbackground")
            self.assertEqual(metadata["KPlugin"]["Name"], "Panel in Background")
            self.assertEqual(self.archive.name,
                             f'plasma-panel-in-background-{metadata["KPlugin"]["Version"]}.plasmoid')
            self.assertEqual(metadata["KPlugin"]["License"], "MIT")
            ET.fromstring(archive.read("contents/config/main.xml"))

    def test_licence_is_bundled_and_consistent(self):
        with zipfile.ZipFile(self.archive) as archive:
            self.assertEqual(archive.read("LICENSE"), (ROOT / "LICENSE").read_bytes())
            self.assertIn(b"MIT License", archive.read("LICENSE"))
            for entry in archive.namelist():
                if entry.endswith((".qml", ".js", ".xml")):
                    self.assertIn(b"SPDX-License-Identifier: MIT", archive.read(entry))
                    self.assertNotIn(b"GPL-2.0-or-later", archive.read(entry))

    def test_checksum(self):
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.assertEqual(self.archive.with_suffix(".plasmoid.sha256").read_text(),
                         f"{digest}  {self.archive.name}\n")

    def test_readme_screenshot_is_bundled(self):
        path = "docs/images/panel-in-background.png"
        with zipfile.ZipFile(self.archive) as archive:
            self.assertIn(path, archive.read("README.md").decode())
            self.assertEqual(archive.read(path), (ROOT / path).read_bytes())
            self.assertTrue(archive.read(path).startswith(b"\x89PNG\r\n\x1a\n"))

    def test_reproducible(self):
        another = builder.build(Path(self.directory.name) / "second")
        self.assertEqual(self.archive.read_bytes(), another.read_bytes())


if __name__ == "__main__":
    unittest.main()
