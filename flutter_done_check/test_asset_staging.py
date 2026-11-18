#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    script = ROOT / "flutter-engine-runner/scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load_script("prepare_asset_staging.py")
validate = load_script("validate_asset_staging.py")


class AssetStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = self.base / "flutter-app"
        self.project.mkdir()
        self.downloads = self.base / "Downloads"
        self.downloads.mkdir()

    def test_prepare_creates_one_project_root_and_required_subdirectories(self):
        report = prepare.prepare(
            project_root=self.project,
            project_name="Bright Harbor / Journal",
            downloads_root=self.downloads,
        )
        self.assertEqual(report["status"], "Prepared")
        staging = Path(report["staging_root"])
        self.assertEqual(staging.parent, self.downloads.resolve())
        self.assertEqual(staging.name, "Bright_Harbor_Journal")
        for name in ("logo-candidates", "backgrounds", "content", "exports"):
            self.assertTrue((staging / name).is_dir())
        manifest = self.project / ".codex-work/asset-staging.json"
        self.assertTrue(manifest.is_file())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(Path(data["staging_root"]), staging)
        self.assertEqual(data["project_root"], str(self.project.resolve()))

    def test_validator_accepts_assets_only_inside_the_managed_root(self):
        prepare.prepare(
            project_root=self.project,
            project_name="Bright Harbor",
            downloads_root=self.downloads,
        )
        staging = self.downloads / "Bright_Harbor"
        (staging / "logo-candidates" / "c01").mkdir()
        (staging / "logo-candidates" / "c01" / "Bright Harbor.png").write_bytes(b"png")
        report = validate.validate(self.project)
        self.assertEqual(report["status"], "Passed", report)

    def test_validator_rejects_file_dropped_at_public_download_root(self):
        prepare.prepare(
            project_root=self.project,
            project_name="Bright Harbor",
            downloads_root=self.downloads,
        )
        (self.downloads / "loose-image.png").write_bytes(b"png")
        report = validate.validate(self.project)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("public Downloads" in error for error in report["errors"]))

    def test_validator_rejects_unmanaged_staging_subdirectory(self):
        prepare.prepare(
            project_root=self.project,
            project_name="Bright Harbor",
            downloads_root=self.downloads,
        )
        staging = self.downloads / "Bright_Harbor"
        (staging / "other-project").mkdir()
        (staging / "other-project" / "foreign.png").write_bytes(b"png")
        report = validate.validate(self.project)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("unmanaged" in error for error in report["errors"]))

    def test_validator_rejects_staging_inside_project_root(self):
        manifest_dir = self.project / ".codex-work"
        manifest_dir.mkdir()
        staging = self.project / "Downloads" / "Bright_Harbor"
        for name in ("logo-candidates", "backgrounds", "content", "exports"):
            (staging / name).mkdir(parents=True)
        (manifest_dir / "asset-staging.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "project_name": "Bright Harbor",
                    "sanitized_project_name": "Bright_Harbor",
                    "project_root": str(self.project.resolve()),
                    "downloads_root": str((self.project / "Downloads").resolve()),
                    "staging_root": str(staging.resolve()),
                    "managed_subdirectories": {
                        "logo_candidates": "logo-candidates",
                        "backgrounds": "backgrounds",
                        "content": "content",
                        "exports": "exports",
                    },
                    "status": "active",
                }
            ),
            encoding="utf-8",
        )
        report = validate.validate(self.project)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("inside the project" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
