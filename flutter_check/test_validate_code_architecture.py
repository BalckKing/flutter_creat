#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_code_architecture.py"
spec = importlib.util.spec_from_file_location("validate_code_architecture", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CodeArchitectureChecks(unittest.TestCase):
    def make_project(self, route="navigator", storage="shared_preferences", architecture="mvvm"):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "lib").mkdir()
        (root / ".codex-work").mkdir()

        if architecture == "mvvm":
            paths = [
                "lib/views/home_view.dart",
                "lib/view_models/home_view_model.dart",
                "lib/repositories/home_repository.dart",
                "lib/models/home_model.dart",
            ]
            dart = """import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
class HomeView extends StatelessWidget { const HomeView({super.key}); @override Widget build(BuildContext context) => const Text('Home'); }
class HomeViewModel { }
class HomeRepository { }
class HomeModel { }
"""
        elif architecture == "mvc":
            paths = [
                "lib/views/home_view.dart",
                "lib/controllers/home_controller.dart",
                "lib/models/home_model.dart",
                "lib/repositories/home_repository.dart",
            ]
            dart = """import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
class HomeView extends StatelessWidget { const HomeView({super.key}); @override Widget build(BuildContext context) => const Text('Home'); }
class HomeController { }
class HomeModel { }
class HomeRepository { }
"""
        else:
            paths = [
                "lib/views/home_view.dart",
                "lib/interactors/home_interactor.dart",
                "lib/presenters/home_presenter.dart",
                "lib/entities/home_entity.dart",
                "lib/routers/home_router.dart",
            ]
            dart = """import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sqflite/sqflite.dart';
class HomeView extends StatelessWidget { const HomeView({super.key}); @override Widget build(BuildContext context) => const Text('Home'); }
class HomeInteractor { }
class HomePresenter { }
class HomeEntity { }
class HomeRouter { }
"""

        for path in paths:
            file = root / path
            file.parent.mkdir(parents=True, exist_ok=True)
            class_name = "".join(part.title() for part in file.stem.split("_"))
            file.write_text(f"class {class_name} {{ }}\n", encoding="utf-8")

        if route == "navigator":
            route_code = """import 'package:flutter/material.dart';
void main() => runApp(MaterialApp(home: Builder(builder: (context) => TextButton(
  onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const Text('Next'))),
  child: const Text('Continue'),
))));
"""
            route_dep = ""
        elif route == "getx":
            route_code = """import 'package:flutter/material.dart';
import 'package:get/get.dart';
class AppController extends GetxController { }
void main() => runApp(GetMaterialApp(home: TextButton(
  onPressed: () => Get.to(() => const Text('Next')),
  child: const Text('Continue'),
)));
"""
            route_dep = "  get: ^4.6.6\n"
        else:
            route_code = """import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
final router = GoRouter(routes: [
  GoRoute(path: '/', builder: (_, __) => const Text('Home')),
  GoRoute(path: '/next', builder: (_, __) => const Text('Next')),
]);
void main() => runApp(MaterialApp.router(routerConfig: router));
"""
            route_dep = "  go_router: ^14.0.0\n"

        if storage == "shared_preferences":
            storage_code = """import 'package:shared_preferences/shared_preferences.dart';
Future<void> savePreference() async { final prefs = await SharedPreferences.getInstance(); await prefs.setBool('ready', true); }
"""
            storage_dep = "  shared_preferences: ^2.2.3\n"
            storage_entry = {
                "kind": "shared_preferences",
                "purpose": "onboarding and non-sensitive preferences",
                "package": "shared_preferences",
                "version": "2.2.3",
                "actual_consumer": ["lib/data/preferences_store.dart"],
                "runtime_evidence": [".codex-work/storage.mp4"],
            }
            storage_path = root / "lib/data/preferences_store.dart"
        elif storage == "flutter_secure_storage":
            storage_code = """import 'package:flutter_secure_storage/flutter_secure_storage.dart';
Future<void> saveSecret() => const FlutterSecureStorage().write(key: 'token', value: 'secret');
"""
            storage_dep = "  flutter_secure_storage: ^9.2.2\n"
            storage_entry = {
                "kind": "flutter_secure_storage",
                "purpose": "private token storage",
                "package": "flutter_secure_storage",
                "version": "9.2.2",
                "actual_consumer": ["lib/data/secret_store.dart"],
                "runtime_evidence": [".codex-work/storage.mp4"],
            }
            storage_path = root / "lib/data/secret_store.dart"
        else:
            storage_code = """import 'package:sqflite/sqflite.dart';
Future<Database> openStore() => openDatabase('app.db');
"""
            storage_dep = "  sqflite: ^2.3.3\n"
            storage_entry = {
                "kind": "sqlite",
                "purpose": "structured offline records",
                "package": "sqflite",
                "version": "2.3.3",
                "actual_consumer": ["lib/data/app_database.dart"],
                "runtime_evidence": [".codex-work/storage.mp4"],
            }
            storage_path = root / "lib/data/app_database.dart"

        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(storage_code, encoding="utf-8")
        (root / "lib/main.dart").write_text(route_code + dart, encoding="utf-8")
        (root / ".codex-work/storage.mp4").write_bytes(b"evidence")
        (root / ".codex-work/navigation.mp4").write_bytes(b"evidence")
        (root / "pubspec.yaml").write_text(
            "name: demo\ndependencies:\n  flutter:\n    sdk: flutter\n" + route_dep + storage_dep,
            encoding="utf-8",
        )

        architecture_files = paths
        manifest = {
            "schema_version": 1,
            "architecture": {
                "style": architecture,
                "rationale": "The feature boundaries match the product state flow.",
                "evidence": architecture_files,
            },
            "routing": {
                "kind": route,
                "package": "flutter" if route == "navigator" else ("get" if route == "getx" else "go_router"),
                "version": "sdk" if route == "navigator" else ("4.6.6" if route == "getx" else "14.0.0"),
                "actual_consumer": ["lib/main.dart"],
                "entrypoint": "lib/main.dart",
                "return_behavior": "Each primary route has an explicit back path.",
                "runtime_evidence": [".codex-work/navigation.mp4"],
            },
            "storage": [storage_entry],
        }
        (root / ".codex-work/code-architecture.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return root

    def test_accepts_native_navigator_mvvm_and_shared_preferences(self):
        report = module.validate(self.make_project())
        self.assertEqual(report, [])

    def test_accepts_getx_mvc_and_secure_storage(self):
        report = module.validate(self.make_project(route="getx", storage="flutter_secure_storage", architecture="mvc"))
        self.assertEqual(report, [])

    def test_accepts_go_router_viper_and_sqlite(self):
        report = module.validate(self.make_project(route="go_router", storage="sqlite", architecture="viper"))
        self.assertEqual(report, [])

    def test_rejects_missing_architecture_manifest(self):
        root = self.make_project()
        (root / ".codex-work/code-architecture.json").unlink()
        report = module.validate(root)
        self.assertTrue(any("code-architecture.json" in error for error in report))

    def test_rejects_route_declaration_without_matching_consumer(self):
        root = self.make_project(route="getx")
        (root / "lib/main.dart").write_text(
            "import 'package:flutter/material.dart';\nvoid main() => runApp(const MaterialApp(home: Text('No GetX')));\n",
            encoding="utf-8",
        )
        report = module.validate(root)
        self.assertTrue(any("routing" in error and "getx" in error.lower() for error in report))

    def test_rejects_storage_package_without_real_consumer(self):
        root = self.make_project()
        (root / "lib/data/preferences_store.dart").write_text(
            "import 'package:shared_preferences/shared_preferences.dart';\n", encoding="utf-8"
        )
        report = module.validate(root)
        self.assertTrue(any("shared_preferences" in error for error in report))

    def test_rejects_missing_architecture_boundary(self):
        root = self.make_project()
        (root / "lib/view_models/home_view_model.dart").unlink()
        report = module.validate(root)
        self.assertTrue(any("mvvm" in error.lower() for error in report))

    def test_rejects_version_ranges_instead_of_exact_versions(self):
        root = self.make_project()
        manifest_path = root / ".codex-work/code-architecture.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["routing"]["version"] = "^1.0.0"
        manifest["storage"][0]["version"] = "^2.2.3"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        report = module.validate(root)
        self.assertTrue(any("exact" in error.lower() for error in report))


if __name__ == "__main__":
    unittest.main()
