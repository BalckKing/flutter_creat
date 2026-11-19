#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_flutter_navigation.py"


class RoutingChecks(unittest.TestCase):
    def run_check(self, route, source, pubspec=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "lib").mkdir()
            (root / ".codex-work").mkdir()
            (root / "lib/main.dart").write_text(source, encoding="utf-8")
            (root / "pubspec.yaml").write_text(
                pubspec or "name: demo\ndependencies:\n  flutter:\n    sdk: flutter\n",
                encoding="utf-8",
            )
            (root / ".codex-work/navigation.mp4").write_bytes(b"evidence")
            manifest = {
                "schema_version": 1,
                "architecture": {"style": "mvvm", "rationale": "feature state boundaries", "evidence": ["lib/main.dart"]},
                "routing": {
                    "kind": route,
                    "package": "flutter" if route == "navigator" else ("get" if route == "getx" else "go_router"),
                    "version": "sdk" if route == "navigator" else "1.0.0",
                    "actual_consumer": ["lib/main.dart"],
                    "entrypoint": "lib/main.dart",
                    "return_behavior": "Back returns to the previous route.",
                    "runtime_evidence": [".codex-work/navigation.mp4"],
                },
                "storage": [],
            }
            (root / ".codex-work/code-architecture.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                capture_output=True, text=True, check=False,
            )
            return result

    def test_accepts_native_navigator(self):
        result = self.run_check(
            "navigator",
            """import 'package:flutter/material.dart';
void main() => runApp(MaterialApp(home: Builder(builder: (context) => TextButton(
  onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const Text('Next'))),
  child: const Text('Continue'),
))));
""",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_getx_route(self):
        result = self.run_check(
            "getx",
            """import 'package:flutter/material.dart';
import 'package:get/get.dart';
void main() => runApp(GetMaterialApp(home: TextButton(
  onPressed: () => Get.to(() => const Text('Next')),
  child: const Text('Continue'),
)));
""",
            """name: demo
dependencies:
  flutter:
    sdk: flutter
  get: ^4.6.6
""",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_go_router_route(self):
        result = self.run_check(
            "go_router",
            """import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
final router = GoRouter(routes: [
  GoRoute(path: '/', builder: (_, __) => const Text('Home')),
  GoRoute(path: '/next', builder: (_, __) => const Text('Next')),
]);
void main() => runApp(MaterialApp.router(routerConfig: router));
""",
            """name: demo
dependencies:
  flutter:
    sdk: flutter
  go_router: ^14.0.0
""",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_requires_declared_route_consumer(self):
        result = self.run_check(
            "getx",
            """import 'package:flutter/material.dart';
void main() => runApp(const MaterialApp(home: Text('Ready')));
""",
            """name: demo
dependencies:
  flutter:
    sdk: flutter
  get: ^4.6.6
""",
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("matching route API consumer", result.stdout)

    def test_rejects_mixed_routes(self):
        result = self.run_check(
            "navigator",
            """import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
final router = GoRouter(routes: [GoRoute(path: '/', builder: (_, __) => const Text('Home'))]);
void main() => runApp(MaterialApp(home: Builder(builder: (context) => TextButton(
  onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const Text('Next'))),
  child: const Text('Continue'),
))));
""",
            """name: demo
dependencies:
  flutter:
    sdk: flutter
  go_router: ^14.0.0
""",
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("mixed", result.stdout)

    def test_missing_manifest_is_explicit_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "lib").mkdir()
            (root / "lib/main.dart").write_text("class App {}\n", encoding="utf-8")
            (root / "pubspec.yaml").write_text("name: demo\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("code-architecture.json is required", result.stdout)


if __name__ == "__main__":
    unittest.main()
