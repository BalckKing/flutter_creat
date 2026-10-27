#!/usr/bin/env python3
"""Contract tests for the final App Review Remarks validator."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_review_remarks.py"


CLEAN = """# App Review Remarks
App name: Saene
Purpose: Explain verified production concepts and private observations.
Category: Popular Science
User-generated content: No public content; private notes only.
Account: No such feature
Billing: No such feature
Permissions: No protected permissions are used.
Other submission details: Local content only.

## 1. Actual Device
- iPhone 17 Pro Max, iOS 26.5

## 2. Test Devices and Operating Systems
- iPhone 15 Pro, iOS 18.6 completed launch and core-flow checks.
- iPhone 13, iOS 17.7.1 completed launch and core-flow checks.

## 3. App Purpose, Intended Audience, and Problem Solved
- The app helps readers organize verified production observations.

## 4. Setup Steps
1. Install and launch the app.
2. Tap Continue to open the main feature.
3. Open Settings, tap Clear Data and confirm in the dialog to return to Initialization.

## 5. External Services
- Advertising: Not used.
- AI services: Not used.
- Third-party SDKs: Not used.

## 6. Regional Differences
- All regions are the same.

## 7. Unique Value
- It connects short lessons with private, revisit-able observations.
"""


class ReviewRemarksChecks(unittest.TestCase):
    def run_check(self, source):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "remarks.md"
            path.write_text(source, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), "--remarks-file", str(path)],
                capture_output=True, text=True, check=False,
            )

    def test_accepts_current_contract(self):
        result = self.run_check(CLEAN)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_pending_unknowns_and_non_iphone_devices(self):
        bad = CLEAN.replace("All regions are the same.", "Not provided; pending confirmation.")
        bad = bad.replace("iPhone 13, iOS 17.7.1", "iPad (10th generation), iPadOS 18.6")
        result = self.run_check(bad)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("unconfirmed or missing information", result.stdout.lower())
        self.assertIn("non-iPhone", result.stdout)

    def test_rejects_embedded_browser_terms_cjk_bold_and_long_copy(self):
        examples = (
            CLEAN.replace("Local content only.", "WebView presents the policy.", 1),
            CLEAN.replace("Local content only.", "中文", 1),
            CLEAN.replace("Local content only.", "**bold**", 1),
            CLEAN + "\n" + ("x" * 4001),
        )
        for source in examples:
            with self.subTest(source=source[:40]):
                result = self.run_check(source)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_rejects_heading_order_or_non_bulleted_section(self):
        bad = CLEAN.replace("## 6. Regional Differences", "## 6. Wrong Heading")
        result = self.run_check(bad)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_omits_unknown_basic_fields_and_device_records(self):
        text = CLEAN.replace('Other submission details: Local content only.\n', '')
        text = text.replace('Billing: No such feature\n', '')
        text = text.replace('- iPhone 15 Pro, iOS 18.6 completed launch and core-flow checks.\n', '')
        text = text.replace('- iPhone 13, iOS 17.7.1 completed launch and core-flow checks.\n', '')
        result = self.run_check(text)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_does_not_accept_other_text_in_fixed_sections(self):
        for text in (
            CLEAN.replace('- All regions are the same.', '- All regions are the same. Except for different prices.'),
            CLEAN.replace('- iPhone 17 Pro Max, iOS 26.5', '- iPhone 17 Pro Max, iOS 26.5\n- iPhone 16, iOS 18.6'),
            CLEAN.replace('Account: No such feature', 'Account: No such feature **'),
        ):
            with self.subTest(text=text[:80]):
                result = self.run_check(text)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
