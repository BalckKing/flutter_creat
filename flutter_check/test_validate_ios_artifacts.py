#!/usr/bin/env python3
import importlib.util, plistlib, tempfile, unittest
from pathlib import Path
SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_ios_artifacts.py"
spec=importlib.util.spec_from_file_location("validate_ios_artifacts", SCRIPT); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
PODFILE="platform :ios, '15.6'\npost_install do |installer|\nend\n"
class IOSArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root=Path(self.temp.name)
        (self.root/"pubspec.yaml").write_text("name: demo\n", encoding="utf-8")
        (self.root/"ios/Runner").mkdir(parents=True); (self.root/"ios/Flutter").mkdir(parents=True)
        (self.root/"ios/Runner/Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier":"com.example.demo"}))
        (self.root/"ios/Flutter/AppFrameworkInfo.plist").write_bytes(plistlib.dumps({"MinimumOSVersion":"15.6"}))
        (self.root/"ios/Podfile").write_text(PODFILE, encoding="utf-8")
    def test_source_passes_but_artifact_is_not_verified(self):
        report=module.validate(self.root)
        self.assertEqual(report["status"], "Not verified", report)
        self.assertEqual(next(c for c in report["checks"] if c["name"]=="MinimumOSVersion source")["status"], "Passed")
    def test_read_write_requires_photo_macro(self):
        report=module.validate(self.root, photo_access="read-write")
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("PERMISSION_PHOTOS=1" in e for e in report["errors"]))
        (self.root/"ios/Podfile").write_text(PODFILE + "# PERMISSION_PHOTOS=1\n", encoding="utf-8")
        report=module.validate(self.root, photo_access="read-write")
        self.assertEqual(report["status"], "Not verified", report)
    def test_att_and_minimum_version_are_blockers(self):
        (self.root/"ios/Runner/AppDelegate.swift").write_text("ATTrackingManager.requestTrackingAuthorization()", encoding="utf-8")
        (self.root/"ios/Flutter/AppFrameworkInfo.plist").write_bytes(plistlib.dumps({"MinimumoSVersion":"15.6"}))
        report=module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("ATT markers" in e for e in report["errors"]))
        self.assertTrue(any("MinimumOSVersion source" in e for e in report["errors"]))

if __name__ == "__main__": unittest.main()
