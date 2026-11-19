#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_quality_records.py"
spec = importlib.util.spec_from_file_location("validate_quality_records", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class QualityRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".codex-work").mkdir()
        (self.root / "assets").mkdir()
        self.asset = self.root / "assets" / "hero.png"
        self.asset.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 32)
        (self.root / ".codex-work" / "evidence.png").write_bytes(b"evidence")

    def record(self):
        digest = hashlib.sha256(self.asset.read_bytes()).hexdigest()
        return {
            "schema_version": 1,
            "run_id": "run-1",
            "resources": [
                {
                    "path": "assets/hero.png",
                    "asset_type": "image",
                    "role": "welcome hero",
                    "source_kind": "generated",
                    "source": "provider task 1",
                    "license": "project-owned generated output",
                    "consumer": "lib/welcome.dart:HeroArtwork",
                    "display_position": "welcome.hero",
                    "sha256": digest,
                    "bytes": self.asset.stat().st_size,
                    "max_bytes": 262144,
                    "status": "Passed",
                    "visual_review": {
                        "subject": "clear hero subject",
                        "material": "layered paper texture",
                        "lighting": "bright rim light",
                        "depth": "foreground and background separation",
                    },
                }
            ],
            "dependencies": [
                {
                    "name": "flutter_animate",
                    "version": "4.5.0",
                    "license": "MIT",
                    "source": "pub.dev",
                    "consumer": "lib/welcome.dart:FadeIn",
                }
            ],
            "accessibility": [
                {
                    "surface": "welcome",
                    "voiceover": "Passed",
                    "dynamic_type": "Passed",
                    "reduce_motion": "Passed",
                    "contrast": "Passed",
                    "evidence": [".codex-work/evidence.png"],
                    "status": "Passed",
                }
            ],
            "resilience": [
                {
                    "scenario": "offline_cold_start",
                    "expected": "bundled content remains visible",
                    "observed": "bundled content remains visible",
                    "evidence": [".codex-work/evidence.png"],
                    "status": "Passed",
                },
                {
                    "scenario": "permission_denied",
                    "expected": "fallback remains usable",
                    "observed": "fallback remains usable",
                    "evidence": [".codex-work/evidence.png"],
                    "status": "Passed",
                },
                {
                    "scenario": "foreground_background",
                    "expected": "state resumes once",
                    "observed": "state resumes once",
                    "evidence": [".codex-work/evidence.png"],
                    "status": "Passed",
                },
                {
                    "scenario": "clear_data_interrupted",
                    "expected": "operation can resume safely",
                    "observed": "operation can resume safely",
                    "evidence": [".codex-work/evidence.png"],
                    "status": "Passed",
                },
            ],
            "security": {"status": "Passed", "evidence": [".codex-work/evidence.png"]},
        }

    def write(self, data):
        (self.root / ".codex-work" / "quality-matrix.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    def test_valid_quality_matrix_passes(self):
        self.write(self.record())
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Passed", report)

    def test_missing_quality_matrix_is_not_verified(self):
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Not verified")

    def test_oversize_or_hash_mismatch_fails(self):
        data = self.record()
        data["resources"][0]["max_bytes"] = 8
        data["resources"][0]["sha256"] = "0" * 64
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("max_bytes" in error for error in report["errors"]))
        self.assertTrue(any("sha256" in error for error in report["errors"]))

    def test_missing_license_consumer_and_matrix_scenario_fail(self):
        data = self.record()
        data["resources"][0]["license"] = ""
        data["dependencies"][0]["consumer"] = "package"
        data["resilience"] = [data["resilience"][0]]
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("license" in error for error in report["errors"]))
        self.assertTrue(any("consumer" in error for error in report["errors"]))
        self.assertTrue(any("permission_denied" in error for error in report["errors"]))

    def test_secret_in_source_fails_security_gate(self):
        (self.root / "lib").mkdir()
        (self.root / "lib" / "config.dart").write_text(
            'const apiKey = "sk-123456789012345678901234";\n', encoding="utf-8"
        )
        data = self.record()
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("secret" in error.lower() for error in report["errors"]))

    def test_project_type_requires_final_visual_product_quality_section(self):
        data = self.record()
        data["project_type"] = "non_game"
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("final_visual_product" in error for error in report["errors"]))

    def test_project_type_with_final_visual_product_quality_section_passes(self):
        data = self.record()
        data["project_type"] = "non_game"
        data["final_visual_product"] = {
            "contract": ".codex-work/final-visual-product.json",
            "status": "Passed",
            "refinement_evidence": [".codex-work/evidence.png"],
            "current_iphone_evidence": [".codex-work/evidence.png"],
        }
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Passed", report)


if __name__ == "__main__":
    unittest.main()
