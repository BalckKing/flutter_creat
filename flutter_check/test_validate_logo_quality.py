#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_logo_quality.py"
spec = importlib.util.spec_from_file_location("validate_logo_quality", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


PNG_RGB = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\x0dIHDR"
    b"\x00\x00\x04\x00\x00\x00\x04\x00\x08\x02\x00\x00\x00"
    b"\x00" * 40
)
PNG_RGBA = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\x0dIHDR"
    b"\x00\x00\x04\x00\x00\x00\x04\x00\x08\x06\x00\x00\x00"
    b"\x00" * 40
)


class LogoQualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "assets").mkdir()
        (self.root / ".codex-work" / "logo").mkdir(parents=True)
        (self.root / "staging" / "project-a").mkdir(parents=True)
        (self.root / "assets/logo.png").write_bytes(PNG_RGB)
        for index in range(1, 13):
            (self.root / f".codex-work/logo/c{index:02d}.png").write_bytes(PNG_RGB)
            (self.root / f"staging/project-a/c{index:02d}.png").write_bytes(PNG_RGB)

    def row(self, index, style):
        path = self.root / f".codex-work/logo/c{index:02d}.png"
        return {
            "id": f"c{index:02d}",
            "style": style,
            "path": path.relative_to(self.root).as_posix(),
            "output_path": f"staging/project-a/c{index:02d}.png",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "status": "Passed",
            "reviewed": True,
            "reviewed_at": "2026-11-18T08:00:00Z",
            "ai_style_risk": "low",
            "reality_logic": "pass",
            "object_integrity": "pass",
            "text_artifacts": "none",
            "material_lighting": "pass",
            "checks": {
                "proportion": "pass",
                "perspective": "pass",
                "contact_and_overlap": "pass",
                "shadow_and_light_direction": "pass",
                "texture_consistency": "pass",
                "object_boundaries": "pass",
            },
            "notes": "Reviewed full-size and icon-size output; no visible generation artifacts.",
            "evidence": [".codex-work/evidence/logo-candidate.png"],
            "generation_task_id": f"task-{index:02d}",
            "project_id": "project-a",
            "source_project_id": "project-a",
            "session_id": "session-a",
            "process_id": "process-a",
            "generation_status": "completed",
            "result_binding": "task_result",
        }

    def manifest(self):
        styles = (
            ["reality-inspired"] * 3
            + ["hand-drawn"] * 3
            + ["oil-painting"] * 3
            + ["artistic-expression"] * 3
        )
        return {
            "schema_version": 1,
            "run_id": "logo-run-1",
            "generated_at": "2026-11-18T08:00:00Z",
            "final_asset": "assets/logo.png",
            "final_sha256": hashlib.sha256((self.root / "assets/logo.png").read_bytes()).hexdigest(),
            "selected_candidate": "c07",
            "generation": {
                "project_id": "project-a",
                "provider": "stargate",
                "provider_url": "http://stargate.local:3100/",
                "session_id": "session-a",
                "process_id": "process-a",
                "exclusive": True,
                "queue_policy": "serialize",
                "status": "completed",
                "staging_root": "staging/project-a",
                "lock_events": [
                    {"event": "acquired", "at": "2026-11-18T07:00:00Z"},
                    {"event": "released", "at": "2026-11-18T08:00:00Z"},
                ],
                "foreign_outputs": [],
            },
            "candidates": [self.row(index, style) for index, style in enumerate(styles, start=1)],
        }

    def write(self, data):
        (self.root / ".codex-work/logo-review.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    def test_valid_review_passes(self):
        self.write(self.manifest())
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Passed", report)

    def test_missing_manifest_is_not_verified(self):
        self.assertEqual(module.validate(self.root)["status"], "Not verified")

    def test_selected_candidate_with_ai_risk_or_logic_failure_is_blocked(self):
        data = self.manifest()
        data["candidates"][6]["ai_style_risk"] = "medium"
        data["candidates"][6]["reality_logic"] = "fail"
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("ai_style_risk" in error for error in report["errors"]))
        self.assertTrue(any("reality_logic" in error for error in report["errors"]))

    def test_style_coverage_and_hash_are_required(self):
        data = self.manifest()
        data["candidates"] = data["candidates"][:-1]
        data["candidates"][0]["sha256"] = "0" * 64
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("12" in error or "style" in error for error in report["errors"]))
        self.assertTrue(any("sha256" in error for error in report["errors"]))

    def test_final_logo_must_be_rgb_png(self):
        (self.root / "assets/logo.png").write_bytes(PNG_RGBA)
        data = self.manifest()
        data["final_sha256"] = hashlib.sha256((self.root / "assets/logo.png").read_bytes()).hexdigest()
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("alpha" in error.lower() for error in report["errors"]))

    def test_generation_session_is_required_and_isolated(self):
        data = self.manifest()
        data["generation"]["exclusive"] = False
        data["candidates"][0]["process_id"] = "process-b"
        data["candidates"][1]["source_project_id"] = "other-project"
        data["generation"]["foreign_outputs"] = [{"project_id": "other-project"}]
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("exclusive" in error for error in report["errors"]))
        self.assertTrue(any("process_id" in error for error in report["errors"]))
        self.assertTrue(any("source_project_id" in error for error in report["errors"]))
        self.assertTrue(any("foreign" in error for error in report["errors"]))

    def test_foreign_or_failed_output_cannot_pass(self):
        data = self.manifest()
        data["generation"]["status"] = "blocked"
        data["candidates"][3]["generation_status"] = "unknown"
        data["candidates"][3]["output_path"] = "staging/other-project/c04.png"
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("generation.status" in error for error in report["errors"]))
        self.assertTrue(any("generation_status" in error for error in report["errors"]))
        self.assertTrue(any("output_path" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
