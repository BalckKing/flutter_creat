#!/usr/bin/env python3
"""Regression fixtures for the project-level game design contract."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_game_design_contract.py"


class GameDesignContractFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "Aurora Game"
        (self.root / "lib" / "game").mkdir(parents=True)
        (self.root / "lib" / "pages").mkdir(parents=True)
        (self.root / "assets" / "game").mkdir(parents=True)
        (self.root / ".codex-work").mkdir()
        self.write("pubspec.yaml", "name: aurora_game\ndependencies:\n  flutter:\n    sdk: flutter\n")
        self._write_project_sources()

    def load_module(self):
        spec = importlib.util.spec_from_file_location("validate_game_design_contract", SCRIPT)
        if spec is None or spec.loader is None:
            self.fail(f"cannot load validator at {SCRIPT}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def write(self, relative: str, content: str | bytes):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def _write_project_sources(self):
        self.write(
            "lib/game/harbor_game.dart",
            """
class HarborGame {
  final tide = TideSystem();
  final roadGraph = HarborRoadGraph();
  final actors = HarborActorRenderer();
  void renderTide() {}
  void renderRoadGraph() {}
  void renderActors() {}
}
""",
        )
        self.write(
            "lib/game/market_game.dart",
            """
class MarketGame {
  final weather = WeatherSystem();
  final roadGraph = MarketRoadGraph();
  final actors = MarketActorRenderer();
  void renderWeather() {}
  void renderRoadGraph() {}
  void renderActors() {}
}
""",
        )
        self.write(
            "lib/pages/harbor_page.dart",
            """
class HarborPage {
  static const route = '/play/harbor';
  static const layout = 'harbor-split-map-hud-v1';
}
""",
        )
        self.write(
            "lib/pages/market_page.dart",
            """
class MarketPage {
  static const route = '/play/market';
  static const layout = 'market-street-hud-v1';
}
""",
        )
        for name in (
            "harbor_environment.png",
            "harbor_road.png",
            "harbor_vehicle.png",
            "market_environment.png",
            "market_road.png",
            "market_character.png",
            "shared_shadow.png"):
            self.write(f"assets/game/{name}", b"authored raster fixture")
        self.write(".codex-work/harbor-page.png", b"harbor page capture")
        self.write(".codex-work/market-page.png", b"market page capture")
        self.write(".codex-work/harbor-run.mp4", b"harbor run capture")
        self.write(".codex-work/market-run.mp4", b"market run capture")
        self.write(".codex-work/game-engine.json", json.dumps({"visual_mode": "2.5d"}))

    def _sha256(self, relative: str) -> str:
        return hashlib.sha256((self.root / relative).read_bytes()).hexdigest()

    def contract(self):
        return {
            "schema_version": 1,
            "project_type": "game",
            "project_identity": {
                "version": "1.4.0",
                "bundle_id": "com.example.aurora.game",
                "device": "iPhone 17 Pro",
                "udid": "00008150-001A114E0C91801E",
            },
            "source_of_truth": {
                "id": ".codex-work/game-design-contract.json",
                "version": 1,
                "priority": [
                    "game-design-contract.json",
                    "pages",
                    "domain_render_assets",
                    "evidence",
                    "status",
                ],
                "non_authoritative_sources": [".codex-work/game-engine.json"],
                "conflict_policy": "fail_on_conflict",
            },
            "visual_system": {
                "renderer": "Flame layered scene renderer",
                "projection": "orthographic 2.5D projection",
                "coordinate_system": "world x/y with depth z",
                "camera": {
                    "model": "orthographic parallax camera",
                    "near_clip": 0.1,
                    "far_clip": 100.0,
                },
                "design_tokens": {
                    "depth_unit_px": 24,
                    "shadow_blur_px": 18,
                    "motion_duration_ms": 420,
                },
                "layers": [
                    {"id": "background", "z": 0, "role": "environment and sky"},
                    {"id": "midground", "z": 1, "role": "road and interactive space"},
                    {"id": "foreground", "z": 2, "role": "actors, effects and HUD"},
                ],
                "materials_lighting": {
                    "materials": ["textured asphalt", "painted metal", "fabric"],
                    "lighting": "directional key light with ambient occlusion",
                    "shadows": "contact shadows under actors and vehicles",
                },
                "measurable_thresholds": {
                    "minimum_depth_layers": 3,
                    "minimum_unique_mode_assets": 3,
                    "minimum_motion_duration_ms": 180,
                    "maximum_flat_geometry_ratio": 0.0,
                    "minimum_occlusion_layers": 2,
                },
                "rejection_thresholds": [
                    "reject if depth layers are fewer than 3",
                    "reject if authored assets are replaced by flat geometry",
                    "reject if motion duration is below 180ms",
                ],
            },
            "modes": [
                {
                    "mode_id": "harbor_dawn",
                    "name": "Harbor Dawn",
                    "environment": {
                        "value": "misty harbor at sunrise",
                        "render_consumers": [
                            "lib/game/harbor_game.dart:HarborGame.renderTide",
                        ],
                    },
                    "road_space": {
                        "value": "three-lane dock road with ramps",
                        "render_consumers": [
                            "lib/game/harbor_game.dart:HarborGame.renderRoadGraph",
                        ],
                    },
                    "vehicle_or_character": {
                        "value": "delivery van with painted metal body",
                        "render_consumers": [
                            "lib/game/harbor_game.dart:HarborGame.renderActors",
                        ],
                    },
                    "entities": {
                        "value": "dock workers and cargo crates",
                        "render_consumers": [
                            "lib/game/harbor_game.dart:HarborGame.renderActors",
                        ],
                    },
                    "rules": {
                        "value": "follow tide windows and avoid blocked ramps",
                        "render_consumers": [
                            "lib/game/harbor_game.dart:HarborGame.renderTide",
                        ],
                    },
                    "results": {
                        "value": "delivery success or missed tide",
                        "render_consumers": [
                            "lib/game/harbor_game.dart:HarborGame.renderActors",
                        ],
                    },
                    "assets": [
                        "assets/game/harbor_environment.png",
                        "assets/game/harbor_road.png",
                        "assets/game/harbor_vehicle.png",
                    ],
                },
                {
                    "mode_id": "market_rush",
                    "name": "Market Rush",
                    "environment": {
                        "value": "crowded market street after rain",
                        "render_consumers": [
                            "lib/game/market_game.dart:MarketGame.renderWeather",
                        ],
                    },
                    "road_space": {
                        "value": "narrow market street with crossing zones",
                        "render_consumers": [
                            "lib/game/market_game.dart:MarketGame.renderRoadGraph",
                        ],
                    },
                    "vehicle_or_character": {
                        "value": "runner carrying a bright parcel",
                        "render_consumers": [
                            "lib/game/market_game.dart:MarketGame.renderActors",
                        ],
                    },
                    "entities": {
                        "value": "vendors, umbrellas and moving carts",
                        "render_consumers": [
                            "lib/game/market_game.dart:MarketGame.renderActors",
                        ],
                    },
                    "rules": {
                        "value": "time crossings and keep the parcel dry",
                        "render_consumers": [
                            "lib/game/market_game.dart:MarketGame.renderWeather",
                        ],
                    },
                    "results": {
                        "value": "on-time delivery or soaked parcel",
                        "render_consumers": [
                            "lib/game/market_game.dart:MarketGame.renderActors",
                        ],
                    },
                    "assets": [
                        "assets/game/market_environment.png",
                        "assets/game/market_road.png",
                        "assets/game/market_character.png",
                    ],
                },
            ],
            "asset_pipeline": {
                "offline_assets": [
                    "assets/game/harbor_environment.png",
                    "assets/game/harbor_road.png",
                    "assets/game/harbor_vehicle.png",
                    "assets/game/market_environment.png",
                    "assets/game/market_road.png",
                    "assets/game/market_character.png",
                    "assets/game/shared_shadow.png",
                ],
                "layers": ["background", "midground", "foreground"],
                "transparency": "alpha premultiplied for sprites and effects",
                "occlusion_order": ["background", "midground", "foreground", "effects", "hud"],
                "coordinate_system": "world x/y with depth z",
                "load_entrypoints": [
                    "lib/game/harbor_game.dart:HarborGame",
                    "lib/game/market_game.dart:MarketGame",
                ],
                "assets": [
                    {
                        "path": "assets/game/harbor_environment.png",
                        "role": "authored environment",
                        "geometry": "layered silhouette",
                        "material": "textured mist and metal",
                        "render_layer": "background",
                        "placeholder": False,
                    },
                    {
                        "path": "assets/game/harbor_road.png",
                        "role": "authored road space",
                        "geometry": "perspective road mesh",
                        "material": "textured asphalt",
                        "render_layer": "midground",
                        "placeholder": False,
                    },
                    {
                        "path": "assets/game/harbor_vehicle.png",
                        "role": "authored vehicle",
                        "geometry": "beveled vehicle silhouette",
                        "material": "painted metal",
                        "render_layer": "foreground",
                        "placeholder": False,
                    },
                ],
                "forbidden": ["placeholder", "solid_color_block", "flat_rectangle", "static_screenshot"],
            },
            "pages": [
                {
                    "page_id": "harbor_play",
                    "route": "/play/harbor",
                    "route_source": "lib/pages/harbor_page.dart",
                    "layout_signature": "harbor-split-map-hud-v1",
                    "composition": "wide harbor horizon with diagonal dock road",
                    "assets": ["assets/game/harbor_environment.png", "assets/game/harbor_road.png"],
                    "states": ["loading", "ready", "success", "failure", "restart"],
                    "interactions": ["tap road", "drag camera", "restart run"],
                    "error_recovery": "restore last checkpoint and show retry action",
                    "evidence": ["evidence.harbor_page_capture"],
                },
                {
                    "page_id": "market_play",
                    "route": "/play/market",
                    "route_source": "lib/pages/market_page.dart",
                    "layout_signature": "market-street-hud-v1",
                    "composition": "compressed market street with layered umbrellas",
                    "assets": ["assets/game/market_environment.png", "assets/game/market_road.png"],
                    "states": ["loading", "ready", "success", "failure", "restart"],
                    "interactions": ["tap crossing", "hold parcel", "restart run"],
                    "error_recovery": "restore parcel checkpoint and show retry action",
                    "evidence": ["evidence.market_page_capture"],
                },
            ],
            "evidence": [
                {
                    "evidence_id": "harbor_page_capture",
                    "acceptance_item": "harbor_play page route and layout",
                    "path": ".codex-work/harbor-page.png",
                    "type": "screenshot",
                    "project_version": "1.4.0",
                    "bundle_id": "com.example.aurora.game",
                    "device": "iPhone 17 Pro",
                    "udid": "00008150-001A114E0C91801E",
                    "status": "Verified",
                    "sha256": "PLACEHOLDER_HASH_HARBOR_PAGE",
                    "page_id": "harbor_play",
                },
                {
                    "evidence_id": "market_page_capture",
                    "acceptance_item": "market_play page route and layout",
                    "path": ".codex-work/market-page.png",
                    "type": "screenshot",
                    "project_version": "1.4.0",
                    "bundle_id": "com.example.aurora.game",
                    "device": "iPhone 17 Pro",
                    "udid": "00008150-001A114E0C91801E",
                    "status": "Verified",
                    "sha256": "PLACEHOLDER_HASH_MARKET_PAGE",
                    "page_id": "market_play",
                },
                {
                    "evidence_id": "harbor_run_capture",
                    "acceptance_item": "harbor mode runtime motion",
                    "path": ".codex-work/harbor-run.mp4",
                    "type": "recording",
                    "project_version": "1.4.0",
                    "bundle_id": "com.example.aurora.game",
                    "device": "iPhone 17 Pro",
                    "udid": "00008150-001A114E0C91801E",
                    "status": "Verified",
                    "sha256": "PLACEHOLDER_HASH_HARBOR_RUN",
                    "mode_id": "harbor_dawn",
                },
                {
                    "evidence_id": "market_run_capture",
                    "acceptance_item": "market mode runtime motion",
                    "path": ".codex-work/market-run.mp4",
                    "type": "recording",
                    "project_version": "1.4.0",
                    "bundle_id": "com.example.aurora.game",
                    "device": "iPhone 17 Pro",
                    "udid": "00008150-001A114E0C91801E",
                    "status": "Verified",
                    "sha256": "PLACEHOLDER_HASH_MARKET_RUN",
                    "mode_id": "market_rush",
                },
            ],
            "status": {
                "plan_status": "Approved",
                "implementation_status": "Implemented",
                "verification_status": "Verified",
                "release_status": "Ready",
            },
            "rejection_rules": [
                "missing independent mode scene",
                "domain field without render consumer",
                "mode changes only copy or color",
                "missing collision causality",
                "placeholder asset",
                "flat geometry",
                "duplicate evidence",
                "static image used as motion evidence",
                "unimplemented route",
                "stale device or build evidence",
            ],
        }

    def write_contract(self, contract=None):
        contract = contract or self.contract()
        for item in contract["evidence"]:
            item["sha256"] = self._sha256(item["path"])
        self.write(".codex-work/game-design-contract.json", json.dumps(contract, indent=2))

    def test_valid_contract_with_two_modes_passes(self):
        self.write_contract()
        findings = self.load_module().validate_project(self.root)
        self.assertEqual(findings, [], findings)

    def test_missing_contract_is_reported(self):
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("game-design-contract.json" in item and "missing" in item for item in findings), findings)

    def test_conflicting_source_of_truth_is_rejected(self):
        contract = self.contract()
        self.write_contract(contract)
        self.write(".codex-work/game-engine.json", json.dumps({"visual_mode": "3d"}))
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("conflict" in item.lower() or "source of truth" in item.lower() for item in findings), findings)

    def test_measurable_visual_thresholds_are_required(self):
        contract = self.contract()
        contract["visual_system"].pop("measurable_thresholds")
        self.write_contract(contract)
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("threshold" in item.lower() or "measurable" in item.lower() for item in findings), findings)

    def test_every_mode_domain_field_requires_render_consumers(self):
        contract = self.contract()
        contract["modes"][0]["road_space"]["render_consumers"] = []
        self.write_contract(contract)
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("render" in item.lower() and "consumer" in item.lower() for item in findings), findings)

    def test_placeholder_and_flat_geometry_assets_are_rejected(self):
        contract = self.contract()
        asset = contract["asset_pipeline"]["assets"][0]
        asset["path"] = "assets/game/placeholder_rect.png"
        asset["geometry"] = "flat_rectangle"
        self.write(asset["path"], b"placeholder fixture")
        self.write_contract(contract)
        findings = self.load_module().validate_project(self.root)
        joined = " ".join(findings).lower()
        self.assertTrue("placeholder" in joined or "flat" in joined or "geometry" in joined, findings)

    def test_missing_route_and_page_evidence_are_rejected(self):
        contract = self.contract()
        contract["pages"][0]["route_source"] = "lib/pages/missing_page.dart"
        contract["pages"][0]["evidence"] = []
        self.write_contract(contract)
        findings = self.load_module().validate_project(self.root)
        joined = " ".join(findings).lower()
        self.assertTrue("route" in joined or "page" in joined, findings)
        self.assertIn("evidence", joined)

    def test_duplicate_evidence_is_rejected(self):
        contract = self.contract()
        contract["evidence"][1]["evidence_id"] = contract["evidence"][0]["evidence_id"]
        self.write_contract(contract)
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("duplicate" in item.lower() and "evidence" in item.lower() for item in findings), findings)

    def test_stale_device_or_build_evidence_is_rejected(self):
        contract = self.contract()
        contract["evidence"][0]["device"] = "iPhone 14 Pro"
        contract["evidence"][1]["project_version"] = "1.3.0"
        self.write_contract(contract)
        findings = self.load_module().validate_project(self.root)
        joined = " ".join(findings).lower()
        self.assertTrue("stale" in joined or "device" in joined or "version" in joined, findings)

    def test_status_contradictions_are_rejected(self):
        contract = self.contract()
        contract["status"]["verification_status"] = "Blocked"
        contract["status"]["release_status"] = "Ready"
        self.write_contract(contract)
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("status" in item.lower() and ("release" in item.lower() or "verification" in item.lower()) for item in findings), findings)


if __name__ == "__main__":
    unittest.main()
