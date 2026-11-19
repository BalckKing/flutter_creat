#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_final_visual_product.py"
spec = importlib.util.spec_from_file_location("validate_final_visual_product", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class FinalVisualProductFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".codex-work" / "final-visual").mkdir(parents=True)
        (self.root / "assets" / "game").mkdir(parents=True)
        (self.root / "assets" / "domain").mkdir(parents=True)
        self.write(".codex-work/final-visual-product.md", "final visual review")
        self.write(".codex-work/final-visual/iphone-recording.mp4", b"recording")
        self.write(".codex-work/final-visual/iphone-screenshot.png", b"screenshot")
        for name in ("hero.png", "environment.png", "prop.png", "effect.png"):
            self.write(f"assets/game/{name}", b"authored asset")
        for name in ("domain-a.png", "domain-b.png", "domain-c.png"):
            self.write(f"assets/domain/{name}", b"domain asset")

    def write(self, relative: str, content: str | bytes):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def common(self):
        return {
            "no_simple_line_art": True,
            "no_flat_color_blocks": True,
            "no_solid_color_background": True,
            "no_placeholder_or_static_mock": True,
            "authored_asset_review": "Verified",
            "composition_review": "Verified",
            "motion_review": "Verified",
            "state_coverage_review": "Verified",
            "accessibility_review": "Verified",
            "refinement_rounds": 3,
            "current_iphone_evidence": [".codex-work/final-visual/iphone-recording.mp4"],
        }

    def game_visual(self):
        return {
            "visual_mode": "3d",
            "renderer": "PBR scene renderer with iOS runtime adapter",
            "camera_model": "perspective camera with authored occlusion and parallax",
            "depth_layers": ["lit environment", "interactive midground", "foreground subject and effects"],
            "materials_lighting": "textured materials, directional light, contact shadows and ambient occlusion",
            "state_variants": "idle, active, success, failure and restart use authored visual variants",
            "animation_feedback": "character motion, camera response, impact particles and result transition",
            "hud_hierarchy": "goal, score, state feedback and controls have independent readable layers",
            "content_scope": "three completed scenarios with distinct authored environments and outcomes",
            "authored_assets": [
                "assets/game/hero.png",
                "assets/game/environment.png",
                "assets/game/prop.png",
                "assets/game/effect.png",
            ],
            "runtime_evidence": [".codex-work/final-visual/iphone-recording.mp4"],
        }

    def non_game_visual(self):
        return {
            "primary_domain": "travel",
            "visual_language": "spatial editorial travel atlas with layered map, route and memory compositions",
            "page_compositions": ["spatial discovery", "route editing", "field memory review"],
            "result_surfaces": ["route map", "day timeline", "memory gallery"],
            "state_coverage": "loading, empty, permission denied, offline, error and completed route states are designed and observed",
            "ui_component_consumers": [
                {
                    "name": "MapKit",
                    "version": "iOS SDK",
                    "license/source": "Apple SDK",
                    "actual_consumer": "lib/page_module/route/route_page.dart:MapView",
                    "runtime_evidence": [".codex-work/final-visual/iphone-recording.mp4"],
                },
                {
                    "name": "fl_chart",
                    "version": "0.69.0",
                    "license/source": "MIT / pub.dev",
                    "actual_consumer": "lib/page_module/insights/insights_page.dart:RouteChart",
                    "runtime_evidence": [".codex-work/final-visual/iphone-recording.mp4"],
                },
            ],
            "domain_assets": [
                "assets/domain/domain-a.png",
                "assets/domain/domain-b.png",
                "assets/domain/domain-c.png",
            ],
            "runtime_evidence": [".codex-work/final-visual/iphone-recording.mp4"],
        }

    def contract(self, project_type="game"):
        data = {
            "schema_version": 1,
            "project_type": project_type,
            "claim": "final_visual_product",
            "development_stage": "final_visual_product",
            "prototype_boundary": {"vertical_slice_status": "Passed", "cannot_substitute_for_final": True},
            "common_visual_contract": self.common(),
            "game_visual_contract": self.game_visual() if project_type in {"game", "mixed"} else None,
            "non_game_visual_contract": self.non_game_visual() if project_type in {"non_game", "mixed"} else None,
            "evidence": [".codex-work/final-visual-product.md", ".codex-work/final-visual/iphone-screenshot.png"],
        }
        return data

    def write_contract(self, data):
        self.write(".codex-work/final-visual-product.json", json.dumps(data, indent=2))

    def test_missing_contract_is_reported(self):
        findings = module.validate(self.root)
        self.assertTrue(any("missing" in item for item in findings), findings)

    def test_vertical_slice_cannot_claim_final(self):
        data = self.contract()
        data["claim"] = "functional_prototype"
        data["development_stage"] = "vertical_slice"
        self.write_contract(data)
        findings = module.validate(self.root)
        joined = " ".join(findings)
        self.assertIn("final_visual_product", joined)
        self.assertIn("vertical_slice", joined)

    def test_game_requires_complete_visual_contract(self):
        data = self.contract()
        data["game_visual_contract"]["depth_layers"] = ["background"]
        data["game_visual_contract"]["authored_assets"] = ["assets/game/hero.png"]
        self.write_contract(data)
        findings = module.validate(self.root)
        self.assertTrue(any("depth_layers" in item for item in findings), findings)
        self.assertTrue(any("authored_assets" in item for item in findings), findings)

    def test_non_game_requires_domain_visual_contract(self):
        data = self.contract("non_game")
        data["non_game_visual_contract"]["primary_domain"] = "unknown"
        data["non_game_visual_contract"]["result_surfaces"] = ["one"]
        self.write_contract(data)
        findings = module.validate(self.root)
        self.assertTrue(any("primary_domain" in item for item in findings), findings)
        self.assertTrue(any("result_surfaces" in item for item in findings), findings)

    def test_mixed_requires_both_sections(self):
        data = self.contract("mixed")
        data["non_game_visual_contract"] = None
        self.write_contract(data)
        findings = module.validate(self.root)
        self.assertTrue(any("non_game_visual_contract" in item for item in findings), findings)

    def test_forbidden_low_fidelity_language_is_rejected(self):
        data = self.contract("non_game")
        data["non_game_visual_contract"]["visual_language"] = "functional prototype with placeholder cards"
        self.write_contract(data)
        findings = module.validate(self.root)
        self.assertTrue(any("forbidden" in item for item in findings), findings)

    def test_complete_game_passes(self):
        self.write_contract(self.contract("game"))
        self.assertEqual(module.validate(self.root), [])

    def test_complete_non_game_passes(self):
        self.write_contract(self.contract("non_game"))
        self.assertEqual(module.validate(self.root), [])

    def test_complete_mixed_passes(self):
        self.write_contract(self.contract("mixed"))
        self.assertEqual(module.validate(self.root), [])

    def test_current_iphone_evidence_requires_device_or_capture_marker(self):
        data = self.contract("game")
        data["common_visual_contract"]["current_iphone_evidence"] = [
            ".codex-work/final-visual/review.bin"
        ]
        self.write(".codex-work/final-visual/review.bin", b"evidence")
        data["game_visual_contract"]["runtime_evidence"] = [
            ".codex-work/final-visual/review.bin"
        ]
        self.write_contract(data)
        findings = module.validate(self.root)
        self.assertTrue(any("iPhone" in item or "capture" in item for item in findings), findings)


if __name__ == "__main__":
    unittest.main()
