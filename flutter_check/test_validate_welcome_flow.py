#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_welcome_flow.py"
spec = importlib.util.spec_from_file_location("validate_welcome_flow", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class WelcomeTests(unittest.TestCase):
    def make(self, source, route="navigator", route_source=None, route_dependency=""):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "lib").mkdir()
        (root / "aduit").mkdir()
        (root / ".codex-work").mkdir()
        (root / "lib/welcome.dart").write_text(source, encoding="utf-8")
        (root / "lib/main.dart").write_text(
            route_source
            or """import 'package:flutter/material.dart';
void main() => runApp(MaterialApp(home: Builder(builder: (context) => TextButton(
  onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const Text('Next'))),
  child: const Text('Continue'),
))));
""",
            encoding="utf-8",
        )
        (root / "aduit/welcome.html").write_text("<html></html>", encoding="utf-8")
        (root / ".codex-work/navigation.mp4").write_bytes(b"evidence")
        (root / "pubspec.yaml").write_text(
            "name: demo\ndependencies:\n  flutter:\n    sdk: flutter\n" + route_dependency,
            encoding="utf-8",
        )
        manifest = {
            "schema_version": 1,
            "architecture": {"style": "mvvm", "rationale": "flow boundaries", "evidence": ["lib/main.dart"]},
            "routing": {
                "kind": route,
                "package": "flutter" if route == "navigator" else ("get" if route == "getx" else "go_router"),
                "version": "sdk" if route == "navigator" else "1.0.0",
                "actual_consumer": ["lib/main.dart"],
                "entrypoint": "lib/main.dart",
                "return_behavior": "Back returns to the prior screen.",
                "runtime_evidence": [".codex-work/navigation.mp4"],
            },
            "storage": [],
        }
        (root / ".codex-work/code-architecture.json").write_text(json.dumps(manifest), encoding="utf-8")
        return root

    def test_native_welcome_and_clear_data_entry_pass(self):
        root = self.make("""class WelcomePage {}
void flow() { ClearData(); Navigator.of(context).pushNamed('/entry'); Text('Continue'); Text('Enter'); }
""")
        self.assertEqual(module.validate(root)["status"], "Passed")

    def test_getx_welcome_passes_when_declared(self):
        root = self.make(
            """class WelcomePage {}
void flow() { Text('Continue'); Text('Enter'); }
""",
            route="getx",
            route_source="""import 'package:flutter/material.dart';
import 'package:get/get.dart';
void main() => runApp(GetMaterialApp(home: TextButton(onPressed: () => Get.to(() => const Text('Next')), child: const Text('Continue'))));
""",
            route_dependency="  get: ^4.6.6\n",
        )
        self.assertEqual(module.validate(root)["status"], "Passed")

    def test_go_router_welcome_passes_when_declared(self):
        root = self.make(
            """class WelcomePage {}
void flow() { Text('Continue'); Text('Enter'); }
""",
            route="go_router",
            route_source="""import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
final router = GoRouter(routes: [GoRoute(path: '/', builder: (_, __) => const Text('Home'))]);
void main() => runApp(MaterialApp.router(routerConfig: router));
""",
            route_dependency="  go_router: ^14.0.0\n",
        )
        self.assertEqual(module.validate(root)["status"], "Passed")

    def test_pause_is_rejected(self):
        root = self.make("class WelcomePage {} // Pause\nText('Continue');")
        report = module.validate(root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("pause" in error.lower() for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
