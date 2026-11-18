#!/usr/bin/env python3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_protocol_urls.py"


class ProtocolUrlChecks(unittest.TestCase):
    def make_project(self, project_name="项目A", urls=None, with_webview=True):
        root = Path(tempfile.mkdtemp())
        (root / "pubspec.yaml").write_text("name: demo\n", encoding="utf-8")
        (root / "lib").mkdir()
        webview_import = (
            "import 'package:webview_flutter/webview_flutter.dart';\n"
            if with_webview else ""
        )
        url_source = (
            "final urls = [\n" + "\n".join(repr(u) + "," for u in (urls or [])) + "\n];"
            if with_webview else "final urls = " + repr(list(urls or [])) + ";"
        )
        (root / "lib/policy_page.dart").write_text(
            webview_import + url_source,
            encoding="utf-8",
        )
        (root / "aduit/site").mkdir(parents=True)
        for name in ("PrivacyPolicy.html", "Terms&Conditions.html", "Support.html"):
            (root / "aduit/site" / name).write_text("<html></html>", encoding="utf-8")
        return root

    def run_check(self, root, project_name="项目A"):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(root), "--project-name", project_name],
            capture_output=True, text=True, check=False,
        )

    def test_expands_project_name_and_requires_native_webview(self):
        root = self.make_project(
            urls=[
                "http://项目A/PrivacyPolicy.html",
                "http://项目A/Terms&Conditions.html",
                "http://项目A/Support.html",
            ]
        )
        result = self.run_check(root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_placeholder_urls(self):
        root = self.make_project(
            urls=[
                "http://【项目名称】/PrivacyPolicy.html",
                "http://【项目名称】/Terms&Conditions.html",
                "http://【项目名称】/Support.html",
            ]
        )
        result = self.run_check(root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("placeholder", result.stdout)

    def test_rejects_wrong_project_name_or_missing_page(self):
        root = self.make_project(
            urls=[
                "http://项目B/PrivacyPolicy.html",
                "http://项目A/Terms&Conditions.html",
                "http://项目A/Support.html",
            ]
        )
        (root / "aduit/site/Support.html").unlink()
        result = self.run_check(root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("project name", result.stdout)
        self.assertIn("Support.html", result.stdout)

    def test_requires_in_app_webview_integration_even_when_url_may_fail(self):
        root = self.make_project(
            urls=[
                "http://项目A/PrivacyPolicy.html",
                "http://项目A/Terms&Conditions.html",
                "http://项目A/Support.html",
            ],
            with_webview=False,
        )
        result = self.run_check(root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("in-app WebView", result.stdout)


if __name__ == "__main__":
    unittest.main()
