# SPDX-License-Identifier: MIT
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_release", ROOT / "scripts/prepare_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {"KPlugin": {"Version": "1.2.3"}}
        self.changelog = "# Changelog\n\n## 1.2.3\n\n- New release.\n\n## 1.2.2\n\n- Old.\n"

    def test_extracts_only_matching_version(self):
        self.assertEqual(release.release_notes("v1.2.3", self.metadata, self.changelog),
                         "- New release.\n")

    def test_current_package_has_release_notes(self):
        metadata = json.loads((ROOT / "package/metadata.json").read_text())
        tag = "v" + metadata["KPlugin"]["Version"]
        self.assertTrue(release.release_notes(tag, metadata,
                                             (ROOT / "CHANGELOG.md").read_text()).strip())

    def test_rejects_mismatched_tag(self):
        for tag in ("v1.2.4", "1.2.3", "v1.2.3-other"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release.release_notes(tag, self.metadata, self.changelog)

    def test_rejects_missing_changelog(self):
        with self.assertRaises(ValueError):
            release.release_notes("v1.2.3", self.metadata, "# Changelog\n\n## 1.2.2\n- Old.\n")

    def test_rejects_empty_changelog(self):
        with self.assertRaises(ValueError):
            release.release_notes("v1.2.3", self.metadata, "## 1.2.3\n\n## 1.2.2\n- Old.\n")

    def test_prerelease(self):
        self.metadata["KPlugin"]["Version"] = "1.2.3-rc.1"
        self.assertEqual(release.release_notes("v1.2.3-rc.1", self.metadata,
                                             "## 1.2.3-rc.1\n- Preview.\n"),
                         "- Preview.\n")

    def test_rejects_invalid_version(self):
        self.metadata["KPlugin"]["Version"] = "../invalid"
        with self.assertRaises(ValueError):
            release.release_notes("v../invalid", self.metadata, self.changelog)


if __name__ == "__main__":
    unittest.main()
