#!/usr/bin/env python3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_flutter_navigation.py"


class NativeNavigationChecks(unittest.TestCase):
    def run_check(self, dart, pubspec="name: demo\ndependencies:\n  flutter:\n    sdk: flutter\n"):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "lib").mkdir()
            (root / "lib/main.dart").write_text(dart, encoding="utf-8")
            (root / "pubspec.yaml").write_text(pubspec, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                capture_output=True, text=True, check=False,
            )
            return result

    def test_accepts_native_navigator(self):
        result = self.run_check(
            """import 'package:flutter/material.dart';
void main() => runApp(MaterialApp(home: Builder(builder: (context) => TextButton(
  onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const Text('Next'))),
  child: const Text('Continue'),
))));
"""
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_getx_dependency_and_api(self):
        result = self.run_check(
            """import 'package:flutter/material.dart';
import 'package:get/get.dart';
void main() => runApp(GetMaterialApp(home: Obx(() => Text('Ready'))));
""",
            pubspec="""name: demo
dependencies:
  flutter:
    sdk: flutter
  get: ^4.6.6
""",
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("forbidden", result.stdout)

    def test_requires_native_navigator_usage(self):
        result = self.run_check(
            """import 'package:flutter/material.dart';
void main() => runApp(const MaterialApp(home: Text('Ready')));
"""
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("native Navigator", result.stdout)

    def test_missing_flutter_project_is_explicit_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(Path(directory))],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("pubspec.yaml is required", result.stdout)


if __name__ == "__main__":
    unittest.main()
