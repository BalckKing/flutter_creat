#!/usr/bin/env python3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_public_copy.py"


class PublicCopyChecks(unittest.TestCase):
    def run_check(self, dart="Text('Explore');", html="<p>Explore the app</p>"):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "lib").mkdir()
            (root / "lib/welcome.dart").write_text(dart, encoding="utf-8")
            (root / "AppListing").mkdir()
            (root / "AppListing/welcome.html").write_text(html, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--project-root", str(root)],
                capture_output=True, text=True, check=False,
            )
            return result

    def test_accepts_ordinary_public_copy(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_cjk_and_prohibited_terms(self):
        for dart in ("Text('中文');", "Text('SDK');", "Text('device');", "Text('local');"):
            with self.subTest(dart=dart):
                result = self.run_check(dart=dart)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_rejects_html_accessibility_copy(self):
        result = self.run_check(html='<button aria-label="广告">Continue</button>')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_rejects_separated_or_tag_split_terms(self):
        for html in ("<p>S D K</p>", "<p>S<span>D</span>K</p>", "<p>t e s t i n g</p>"):
            with self.subTest(html=html):
                result = self.run_check(html=html)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_ignores_script_and_style_implementation_text(self):
        result = self.run_check(html='<style>.local{}</style><script>const sdk="SDK";</script><p>Explore</p>')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ignores_dart_identifiers_and_comments(self):
        result = self.run_check(dart="// Text('device')\n/* Text('SDK') */\nimport 'package:demo/main.dart';\nfinal deviceState = 'ready'; Text('Explore');")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_word_fragments_do_not_reject_ordinary_english(self):
        result = self.run_check(dart="Text('A library of botanical illustrations');", html="<p>Explore publication history.</p>")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_nonexistent_project_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(SCRIPT), '--project-root', str(Path(directory) / 'missing')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
