#!/usr/bin/env python3
"""Exercise naming checks on real temporary project trees, without renaming files."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_path_names.py"


class PathNameChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.put("pubspec.yaml", "name: sample\nversion: 1.2.3+45\n")
        self.put(".codex-work/path-terms.json", '{"terms": {}}')

    def put(self, name, content=""):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def run_check(self):
        before = {p.relative_to(self.root).as_posix(): p.read_bytes()
                  for p in self.root.rglob("*") if p.is_file() and not p.is_symlink()}
        run = subprocess.run([sys.executable, str(SCRIPT), "--project-root", str(self.root), "--json"],
                             text=True, capture_output=True, check=False)
        after = {p.relative_to(self.root).as_posix(): p.read_bytes()
                 for p in self.root.rglob("*") if p.is_file() and not p.is_symlink()}
        self.assertEqual(before, after, "validator must not rename or edit project files")
        return run, json.loads(run.stdout)

    def test_rejects_long_parent_and_file_even_without_a_path_inventory(self):
        self.put("lib/services/detail_controller.dart")
        run, report = self.run_check()
        self.assertEqual(run.returncode, 1)
        self.assertTrue(any("lib/services: abbreviate services -> svc" in e for e in report["errors"]))
        self.assertTrue(any("controller -> ctl" in e for e in report["errors"]))
        self.assertIn("lib/services/detail_controller.dart", report["checked"])

    def test_short_names_and_exact_contracts_pass(self):
        for path in ("lib/svc/det_ctl.dart", "lib/common_module/theme/app_theme.dart",
                     "lib/common_module/wgt/card.dart", "lib/page_module/init/init_page.dart",
                     "assets/backgrounds/init/init_background.png", "assets/logo.png",
                     "assets/illustrations/init/intro_ill.png", "lib/welcome.dart",
                     "ios/Runner/AppDelegate.swift", "ios/Runner/Assets.xcassets/Contents.json",
                     "ios/Runner/Base.lproj/LaunchScreen.storyboard"):
            self.put(path)
        run, report = self.run_check()
        self.assertEqual(run.returncode, 0, report)
        self.assertIn("lib/page_module/init/init_page.dart", report["checked"])
        self.assertIn("lib/welcome.dart", report["preserved"])

    def test_fixed_background_pattern_does_not_exempt_long_page_ids(self):
        self.put("assets/backgrounds/initialization/initialization_background.png")
        run, report = self.run_check()
        self.assertEqual(run.returncode, 1)
        self.assertTrue(any("initialization_background.png: abbreviate initialization -> init" in e
                            for e in report["errors"]))

    def test_theme_proper_names_are_checked_using_project_glossary(self):
        self.put(".codex-work/path-terms.json", json.dumps({"terms": {"central_business_district": "cbd"}}))
        self.put("assets/media/central_business_district_cover.jpg")
        run, report = self.run_check()
        self.assertEqual(run.returncode, 1)
        self.assertTrue(any("central_business_district -> cbd" in e for e in report["errors"]))
        (self.root / "assets/media/central_business_district_cover.jpg").rename(self.root / "assets/media/cbd_cover.jpg")
        run, report = self.run_check()
        self.assertEqual(run.returncode, 0, report)

    def test_missing_or_invalid_glossary_cannot_silently_pass(self):
        path = self.root / ".codex-work/path-terms.json"
        for source in (None, "{}", '{"terms": {"configuration": "configuration"}}',
                       '{"terms": {"long_name": "service"}}'):
            with self.subTest(source=source):
                if source is None:
                    path.unlink()
                else:
                    path.write_text(source)
                run, report = self.run_check()
                self.assertEqual(run.returncode, 1)
                self.assertTrue(any("path-terms.json:" in e for e in report["errors"]))

    def test_excluded_tool_and_delivery_roots_do_not_hide_custom_native_or_extra_code(self):
        for path in ("build/services/controller.dart", "ios/Pods/models/Widget.h",
                     "aduit/site/PrivacyPolicy.html", ".codex-work/path-names.md"):
            self.put(path)
        run, report = self.run_check()
        self.assertEqual(run.returncode, 0, report)
        self.put("ios/Runner/feature_controller.swift")
        self.put("custom_tools/configuration.json")
        run, report = self.run_check()
        self.assertEqual(run.returncode, 1)
        self.assertIn("ios/Runner/feature_controller.swift", report["checked"])
        self.assertIn("custom_tools/configuration.json", report["checked"])

    def test_symbolic_link_does_not_hide_uninspected_custom_code(self):
        self.put("lib/app.dart")
        (self.root / "lib/alias").symlink_to(self.root / "lib/app.dart")
        run, report = self.run_check()
        self.assertEqual(run.returncode, 1)
        self.assertTrue(any("uninspected symbolic link" in e for e in report["errors"]))

    def test_ambiguous_or_already_short_names_are_preserved(self):
        self.put("lib/state.dart")
        self.put("assets/guide.jpg")
        self.put("lib/domain/model/schema.dart")
        self.put("lib/domain/model/detail_controller.dart")
        self.put(".codex-work/path-terms.json", json.dumps({"terms": {}, "keep": [{
            "path": "lib/domain/model",
            "reason": "model is a domain term distinct from the abbreviated mdl data layer",
        }]}))
        run, report = self.run_check()
        self.assertEqual(run.returncode, 1)
        self.assertIn("lib/domain/model", report["preserved"])
        self.assertFalse(any("lib/state.dart:" in e or "assets/guide.jpg:" in e for e in report["errors"]))
        # Keeping a directory's own name does not exempt its children's names.
        self.assertTrue(any("detail_controller.dart:" in e for e in report["errors"]))

    def test_keep_cannot_use_a_wildcard_or_omit_a_reason(self):
        self.put("lib/services/app.dart")
        for entry in ({"path": "lib/services", "reason": ""},
                      {"path": "lib/*", "reason": "keep all"}):
            self.put(".codex-work/path-terms.json", json.dumps({"terms": {}, "keep": [entry]}))
            run, report = self.run_check()
            self.assertEqual(run.returncode, 1)
            self.assertTrue(any("path-terms.json:" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
