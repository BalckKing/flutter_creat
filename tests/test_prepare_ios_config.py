#!/usr/bin/env python3
"""Exercise source preparation without building or installing an app."""
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/prepare_ios_config.py"
PODFILE = """platform :ios, '15.6'
post_install do |installer|
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)
    target.build_configurations.each do |config|
      config.build_settings['CUSTOM_SETTING'] = 'preserved'
    end
  end
end
"""


class IOSConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "test app"
        self.root.mkdir()
        (self.root / "pubspec.yaml").write_text("name: fixture\n")
        (self.root / "ios/Flutter").mkdir(parents=True)
        self.framework = self.root / "ios/Flutter/AppFrameworkInfo.plist"
        self.write_plist({"CFBundleExecutable": "App", "CFBundlePackageType": "FMWK"})
        self.podfile = self.root / "ios/Podfile"
        self.podfile.write_text(PODFILE)

    def write_plist(self, data):
        self.framework.write_bytes(plistlib.dumps(data))

    def run_tool(self, *options, expected=0):
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(self.root),
             "--photo-access", "none", *options], capture_output=True, text=True,
        )
        self.assertEqual(process.returncode, expected, process.stdout + process.stderr)
        return json.loads(process.stdout)

    def test_check_detects_missing_key_without_writing(self):
        before = self.framework.read_bytes()
        result = self.run_tool(expected=1)
        self.assertIn("MinimumOSVersion", str(result))
        self.assertEqual(self.framework.read_bytes(), before)
        self.assertFalse((self.root / ".codex-work").exists())

    def test_apply_preserves_keys_backs_up_and_is_idempotent(self):
        before = self.framework.read_bytes()
        result = self.run_tool("--apply")
        data = plistlib.loads(self.framework.read_bytes())
        self.assertEqual(data["MinimumOSVersion"], "15.6")
        self.assertEqual(data["CFBundleExecutable"], "App")
        self.assertFalse(result["build_verified"])
        backups = list((self.root / ".codex-work/ios-config-backup").glob("*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), before)
        current = self.framework.read_bytes()
        self.assertEqual(self.run_tool("--apply")["changed"], [])
        self.assertEqual(self.framework.read_bytes(), current)

    def test_higher_existing_version_is_not_lowered(self):
        self.write_plist({"MinimumOSVersion": "18.0"})
        self.run_tool("--minimum-ios", "17.0", "--apply")
        self.assertEqual(plistlib.loads(self.framework.read_bytes())["MinimumOSVersion"], "18.0")

    def test_incorrect_key_case_is_repaired_without_losing_higher_value(self):
        self.write_plist({"MinimumoSVersion": "17.2", "CFBundleExecutable": "App"})
        self.run_tool("--apply")
        data = plistlib.loads(self.framework.read_bytes())
        self.assertEqual(data["MinimumOSVersion"], "17.2")
        self.assertNotIn("MinimumoSVersion", data)

    def test_invalid_plist_or_version_does_not_get_overwritten(self):
        for content in (b"not a plist", plistlib.dumps({"MinimumOSVersion": "$(UNKNOWN)"})):
            with self.subTest(content=content):
                self.framework.write_bytes(content)
                self.run_tool("--apply", expected=1)
                self.assertEqual(self.framework.read_bytes(), content)

    def test_missing_framework_file_is_reported_instead_of_fabricated(self):
        self.framework.unlink()
        self.run_tool("--apply", expected=1)
        self.assertFalse(self.framework.exists())

    def test_system_picker_does_not_add_permission_macros(self):
        before = self.podfile.read_bytes()
        self.run_tool("--photo-access", "picker", "--apply")
        self.assertEqual(self.podfile.read_bytes(), before)

    @unittest.skipUnless(shutil.which("ruby"), "Ruby is required for CocoaPods preparation")
    def test_read_write_hook_is_idempotent_and_runs_after_existing_settings(self):
        result = self.run_tool("--photo-access", "read-write", "--permission-handler", "--apply")
        self.assertIn("ios/Podfile", result["changed"])
        current = self.podfile.read_bytes()
        self.assertIn(b"PERMISSION_PHOTOS=1", current)
        self.assertEqual(current.count(b"post_install do"), 1)
        self.assertLess(current.index(b"CUSTOM_SETTING"), current.index(b"BEGIN CODEX IOS PERMISSIONS"))
        self.assertEqual(self.run_tool("--photo-access", "read-write", "--permission-handler", "--apply")["changed"], [])
        self.assertEqual(self.podfile.read_bytes(), current)

    @unittest.skipUnless(shutil.which("ruby"), "Ruby is required for CocoaPods preparation")
    def test_hook_changes_real_plugin_configurations_preserving_other_flags(self):
        self.run_tool("--photo-access", "read-write", "--permission-handler", "--apply")
        harness = """require 'json'
Config = Struct.new(:build_settings)
Target = Struct.new(:name, :build_configurations)
configs = [
  Config.new({'GCC_PREPROCESSOR_DEFINITIONS' => ['$(inherited)', 'PERMISSION_PHOTOS=0', 'PERMISSION_CAMERA=1']}),
  Config.new({'GCC_PREPROCESSOR_DEFINITIONS' => 'OTHER=7 PERMISSION_PHOTOS=0 PERMISSION_MICROPHONE=1'}),
  Config.new({})
]
runner = Target.new('Runner', [Config.new({'GCC_PREPROCESSOR_DEFINITIONS' => ['RUNNER_FLAG=1']})])
plugin = Target.new('permission_handler_apple', configs)
$installer = Struct.new(:pods_project).new(Struct.new(:targets).new([runner, plugin]))
def platform(*args); end
def flutter_additional_ios_build_settings(target); end
def post_install; yield $installer; end
load ARGV.fetch(0)
puts JSON.generate({'plugin' => $installer.pods_project.targets[1].build_configurations.map(&:build_settings), 'runner' => $installer.pods_project.targets[0].build_configurations[0].build_settings})
"""
        result = subprocess.run(["ruby", "-e", harness, str(self.podfile)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        settings = json.loads(result.stdout)
        for config in settings["plugin"]:
            definitions = " ".join(config["GCC_PREPROCESSOR_DEFINITIONS"])
            self.assertIn("$(inherited)", definitions)
            self.assertEqual(definitions.count("PERMISSION_PHOTOS=1"), 1)
            self.assertNotIn("PERMISSION_PHOTOS=0", definitions)
            self.assertIn("PERMISSION_APP_TRACKING_TRANSPARENCY=0", definitions)
            self.assertEqual(config["CUSTOM_SETTING"], "preserved")
        self.assertIn("PERMISSION_CAMERA=1", str(settings["plugin"][0]))
        self.assertIn("OTHER=7", str(settings["plugin"][1]))
        self.assertIn("PERMISSION_MICROPHONE=1", str(settings["plugin"][1]))
        self.assertEqual(settings["runner"]["GCC_PREPROCESSOR_DEFINITIONS"], ["RUNNER_FLAG=1"])

    @unittest.skipUnless(shutil.which("ruby"), "Ruby is required for CocoaPods preparation")
    def test_add_only_and_picker_use_their_respective_macros(self):
        self.run_tool("--photo-access", "add-only", "--permission-handler", "--apply")
        self.assertIn("PERMISSION_PHOTOS_ADD_ONLY=1", self.podfile.read_text())
        self.assertIn("PERMISSION_PHOTOS=0", self.podfile.read_text())
        self.run_tool("--photo-access", "picker", "--permission-handler", "--apply")
        self.assertIn("PERMISSION_PHOTOS_ADD_ONLY=0", self.podfile.read_text())
        self.assertIn("PERMISSION_PHOTOS=0", self.podfile.read_text())

    @unittest.skipUnless(shutil.which("ruby"), "Ruby is required for CocoaPods preparation")
    def test_invalid_or_multiple_hooks_are_rejected_without_changes(self):
        for content in ("post_install do |installer|\n", PODFILE + PODFILE):
            with self.subTest(content=content):
                self.podfile.write_text(content)
                self.run_tool("--permission-handler", "--apply", expected=1)
                self.assertEqual(self.podfile.read_text(), content)

    def test_missing_podfile_is_not_replaced_with_an_empty_file(self):
        self.podfile.unlink()
        self.run_tool("--permission-handler", "--apply", expected=1)
        self.assertFalse(self.podfile.exists())

    def test_invalid_podfile_does_not_partially_write_framework(self):
        before = self.framework.read_bytes()
        self.podfile.write_text("post_install do |installer|\n")
        self.run_tool("--permission-handler", "--apply", expected=1)
        self.assertEqual(self.framework.read_bytes(), before)
        self.assertFalse((self.root / ".codex-work").exists())

    def test_minimum_below_workflow_floor_is_rejected(self):
        before = self.framework.read_bytes()
        self.run_tool("--minimum-ios", "12.0", "--apply", expected=1)
        self.assertEqual(self.framework.read_bytes(), before)

    def test_successful_apply_is_followed_by_successful_read_only_check(self):
        self.run_tool("--photo-access", "read-write", "--permission-handler", "--apply")
        result = self.run_tool("--photo-access", "read-write", "--permission-handler")
        self.assertTrue(result["source_ready"])
        self.assertEqual(result["required_changes"], [])
        self.assertEqual(result["changed"], [])
        self.assertFalse(result["build_verified"])

    def test_symlink_backup_directory_is_rejected_before_source_write(self):
        before = self.framework.read_bytes()
        external = Path(self.temp.name) / "outside-backups"
        external.mkdir()
        (self.root / ".codex-work").symlink_to(external, target_is_directory=True)
        self.run_tool("--apply", expected=1)
        self.assertEqual(self.framework.read_bytes(), before)
        self.assertEqual(list(external.iterdir()), [])

    def test_symlink_cannot_write_outside_project(self):
        external = Path(self.temp.name) / "outside.plist"
        original = self.framework.read_bytes()
        external.write_bytes(original)
        self.framework.unlink()
        self.framework.symlink_to(external)
        self.run_tool("--apply", expected=1)
        self.assertEqual(external.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
