#!/usr/bin/env python3

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_about_copy.py"
PAGES = ("index.html", "PrivacyPolicy.html", "Terms&Conditions.html", "Support.html")
CLEAN = """<!doctype html><html><head><title>About the app</title></head><body>
<h1>Explore and record observations</h1><p>Choose a topic and save your observations.
Camera and microphone access are requested when you use their respective actions.
Select Clear Data in Settings to remove saved content. Cancel to keep your data.</p>
<a href="https://Example.invalid/Policy?Mode=Read#Rights">Privacy Policy</a>
</body></html>"""


class AboutCopyChecks(unittest.TestCase):
    def run_check(self, addition="", missing=None):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            for name in PAGES:
                if name != missing:
                    source = CLEAN.replace("</body>", addition + "</body>") if name == "Support.html" else CLEAN
                    (site / name).write_text(source, encoding="utf-8")
            before = {p.name: p.read_bytes() for p in site.iterdir()}
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--site-dir", str(site)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(before, {p.name: p.read_bytes() for p in site.iterdir()})
            return result

    def test_complete_copy_is_accepted_without_modifying_urls(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_publication_status_variants_on_any_page(self):
        examples = (
            "<h2>Publication details — draft</h2><p>This edition is a development distribution. "
            "A verified operator identity, contact channel, and public policy address have not been configured. "
            "These details must be completed before public release. "
            "No contact address or public availability is implied by this page.</p>",
            "<p>A verified operator identity, contact channel, and public policy address have not been configured.</p>",
            "<p>These details must be completed before public release.</p>",
            "<p>No contact address or public availability is implied by this page.</p>",
            "<h2>D<span>r&#97;</span>\u200bFT</h2>",
            '<section hidden>Work in progress</section>',
            '<meta name="description" content="Preview edition">',
            '<img alt="Contact channel is not yet configured" src="img/logo.png">',
            '<button aria-label="Pending confirmation">Continue</button>',
            "<p>发布资料待配置</p>",
        )
        for example in examples:
            with self.subTest(example=example):
                result = self.run_check(example)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("Support.html", result.stdout)

    def test_ignores_internal_code_and_attribute_names(self):
        result = self.run_check(
            '<script>const draft = "internal state";</script>'
            '<style>.draft {color: red}</style><!-- draft status -->'
            '<input id="draft" placeholder="Search saved work">'
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_required_page_is_a_failure(self):
        result = self.run_check(missing="PrivacyPolicy.html")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("PrivacyPolicy.html", result.stdout)


if __name__ == "__main__":
    unittest.main()
