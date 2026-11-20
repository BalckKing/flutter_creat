#!/usr/bin/env python3
"""Regression tests for the game-engine project source preflight."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_game_project.py"


class GameProjectFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "Aurora Game"
        (self.root / "lib").mkdir(parents=True)
        (self.root / "ios").mkdir()
        (self.root / "pubspec.yaml").write_text(
            """name: aurora_game\ndependencies:\n  flutter:\n    sdk: flutter\n  flame: ^1.35.1\n""",
            encoding="utf-8",
        )

    def load_module(self):
        spec = importlib.util.spec_from_file_location("validate_game_project", SCRIPT)
        if spec is None or spec.loader is None:
            self.fail(f"cannot load validator at {SCRIPT}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def write(self, relative: str, content: str | bytes = "fixture"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def write_manifest(self, engine: str = "Flame", **changes):
        if not isinstance(engine, str):
            changes.setdefault("engine", engine)
            engine = "Flame"
        manifest = {
            "project_type": "game",
            "game_lobby": {
                "role": "immersive_game_lobby",
                "mode": "immersive_portrait",
                "orientation": "portrait",
                "entrypoint": "lib/welcome.dart",
                "primary_actions": ["Play", "Load", "Operation"],
                "top_actions": ["Exit", "Settings"],
                "play_flow": ["Play", "Loading", "Game"],
                "load_flow": ["Load", "Save Slot", "Game"],
                "operation_controls": ["Volume", "Graphics Quality"],
                "performance_adaptation": "adapts graphics quality to the selected iPhone performance tier",
                "evidence": [".codex-work/game-lobby.json"],
            },
            "visual_mode": "2.5d",
            "visual_contract": {
                "renderer": "Flame renderer with parallax layers",
                "camera_model": "orthographic camera with perspective parallax",
                "depth_layers": ["background environment", "midground gameplay space", "foreground subject and effects"],
                "materials_lighting": "textured materials, directional light and contact shadows",
                "authored_assets": ["assets/game/hero.png", "assets/game/scene.png"],
                "animation_feedback": "character animation, camera parallax and particle impact",
                "no_flat_color_blocks": True,
            },
            "implementation_mode": "engine",
            "engine_required": True,
            "decision_reason": "Real scene entities and continuous update require an engine.",
            "engine": {
                "name": engine,
                "version": "1.35.1" if engine == "Flame" else "4.7.2",
                "role": "owns the runtime scene, entities, input and rules",
                "integration": "Flutter GameWidget" if engine == "Flame" else "SwiftGodot host and Flutter platform view",
                "entrypoint": "lib/game/game.dart" if engine == "Flame" else "game/scenes/city.tscn",
                "scene_assets": [
                    "assets/game/hero.png",
                    "assets/game/scene.png",
                ] if engine == "Flame" else [
                    "game/project.godot",
                    "game/scenes/city.tscn",
                    "ios/Runner/game.pck",
                    "assets/game/city.png",
                ],
                "runtime_owner": "engine owns input update rules and result state",
                "native_bridge": "not applicable" if engine == "Flame" else "ios/Runner/GodotHost.swift",
                "build_commands": ["flutter build ios --no-codesign"],
                "evidence": [".codex-work/game-runtime.json"],
            },
        }
        for key, value in changes.items():
            if key == "engine":
                manifest["engine"].update(value)
            else:
                manifest[key] = value
        self.write(".codex-work/game-engine.json", json.dumps(manifest, indent=2))
        self.write("lib/welcome.dart", """
class WelcomePage {
  final primaryActions = const ['Play', 'Load', 'Operation'];
  final topActions = const ['Exit', 'Settings'];
  void play() => initializeGame();
  void initializeGame() => showLoading();
  void load() => loadSaveSlot();
  void operation() { setVolume(); setGraphicsQuality(); adaptPerformanceTier(); }
  void exit() {}
  void settings() {}
}
""")
        self.write(".codex-work/game-lobby.json", json.dumps({"device": "iPhone 17 Pro", "recording": ".codex-work/iphone-gameplay-recording.mp4"}))
        return manifest

    def write_native_manifest(self, **changes):
        manifest = {
            "project_type": "game",
            "game_lobby": {
                "role": "immersive_game_lobby",
                "mode": "immersive_portrait",
                "orientation": "portrait",
                "entrypoint": "lib/welcome.dart",
                "primary_actions": ["Play", "Load", "Operation"],
                "top_actions": ["Exit", "Settings"],
                "play_flow": ["Play", "Loading", "Game"],
                "load_flow": ["Load", "Save Slot", "Game"],
                "operation_controls": ["Volume", "Graphics Quality"],
                "performance_adaptation": "adapts graphics quality to the selected iPhone performance tier",
                "evidence": [".codex-work/game-lobby.json"],
            },
            "visual_mode": "2.5d",
            "visual_contract": {
                "renderer": "Flutter 2.5D layered renderer",
                "camera_model": "depth-aware parallax camera",
                "depth_layers": ["background environment", "midground gameplay space", "foreground subject and effects"],
                "materials_lighting": "textured materials, directional light and contact shadows",
                "authored_assets": ["assets/game/cards.png", "assets/game/table.png"],
                "animation_feedback": "card motion, depth parallax and state lighting",
                "no_flat_color_blocks": True,
            },
            "implementation_mode": "flutter-native",
            "engine_required": False,
            "decision_reason": "Turn-based rules are finite state and do not need a continuously simulated world.",
            "engine": None,
            "native_runtime": {
                "entrypoint": ["lib/game/native_game.dart"],
                "scene_assets": ["assets/game/cards.png", "assets/game/table.png"],
                "runtime_owner": "Flutter owns scene, state, input, update, rules, results and restart.",
                "native_bridge": None,
                "animation_effects": ["CustomPainter (Flutter SDK)", "AnimationController (Flutter SDK)"],
                "formula_record": ".codex-work/native-motion.md",
                "evidence": [".codex-work/game-runtime.json"],
            },
        }
        for key, value in changes.items():
            if key == "native_runtime":
                manifest["native_runtime"].update(value)
            else:
                manifest[key] = value
        self.write(".codex-work/game-engine.json", json.dumps(manifest, indent=2))
        return manifest

    def write_native_fixture(self, *, full=True):
        self.write("assets/game/cards.png", b"cards image")
        self.write("assets/game/table.png", b"table image")
        self.write("lib/welcome.dart", """
class WelcomePage {
  final primaryActions = const ['Play', 'Load', 'Operation'];
  final topActions = const ['Exit', 'Settings'];
  void play() => initializeGame();
  void initializeGame() => showLoading();
  void load() => loadSaveSlot();
  void operation() { setVolume(); setGraphicsQuality(); adaptPerformanceTier(); }
  void exit() {}
  void settings() {}
}
""")
        self.write(".codex-work/game-lobby.json", json.dumps({"device": "iPhone 17 Pro", "recording": ".codex-work/iphone-gameplay-recording.mp4"}))
        self.write(".codex-work/native-motion.md", """主题锚点：明亮纸牌桌与材质纹理。\n主体：卡牌、纸张、金属筹码。\n前中后景：桌面、卡列、背景光。\n运动：点击后卡牌翻转并推进回合。\n技术：CustomPainter + AnimationController，0.45s，12px，opacity 0.9。\n循环/完成/中断：完成停留；后台取消；Reduce Motion 淡化。\n负面限制：禁止色块拼贴和静态截图冒充。""")
        source = """
import 'package:flutter/material.dart';
class NativeGame extends StatefulWidget { const NativeGame({super.key}); @override State<NativeGame> createState() => _NativeGameState(); }
class _NativeGameState extends State<NativeGame> with TickerProviderStateMixin, WidgetsBindingObserver {
  late final AnimationController controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 450));
  bool won = false; bool lost = false;
  void onTapUp(TapUpDetails details) { updateRules(); }
  void updateRules() { setState(() { won = true; }); controller.forward(from: 0); }
  void restart() { setState(() { won = false; lost = false; }); }
  @override void didChangeAppLifecycleState(AppLifecycleState state) { if (state == AppLifecycleState.paused) controller.stop(); }
  @override void dispose() { controller.dispose(); super.dispose(); }
  @override Widget build(BuildContext context) => GestureDetector(onTapUp: onTapUp, child: CustomPaint(painter: TablePainter(), child: Stack(children: [Text(won ? 'Success' : 'HUD feedback'), if (lost) const Text('Failure')] )));
}
class TablePainter extends CustomPainter { @override void paint(Canvas c, Size s) {} @override bool shouldRepaint(covariant TablePainter oldDelegate) => true; }
"""
        if not full:
            source = """
import 'package:flutter/material.dart';
class MockNativeGame extends StatelessWidget { const MockNativeGame({super.key}); @override Widget build(BuildContext context) => Container(color: Colors.orange); }
"""
        self.write("lib/game/native_game.dart", source)

    def _write_game_design_contract(self, *, device="iPhone 17 Pro"):
        """Write the shared design contract required by game preflight.

        The game-engine manifest remains the engine decision fixture.  This
        contract mirrors its current visual mode and binds the fixture's
        domain fields, assets, page route and runtime evidence so the new
        single-source gate can pass for the positive engine/native cases.
        """
        manifest_path = self.root / ".codex-work/game-engine.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        visual_mode = manifest.get("visual_mode", "2.5d")
        engine = manifest.get("engine") if isinstance(manifest.get("engine"), dict) else {}
        native_runtime = manifest.get("native_runtime") if isinstance(manifest.get("native_runtime"), dict) else {}
        engine_name = engine.get("name")
        if manifest.get("implementation_mode") == "flutter-native":
            runtime_source = "lib/game/native_game.dart"
            runtime_consumer = "lib/game/native_game.dart:NativeGame"
            scene_values = list(native_runtime.get("scene_assets", []))
        elif engine_name == "Godot":
            runtime_source = "game/scripts/city.gd"
            runtime_consumer = "game/scripts/city.gd:update_rules"
            scene_values = list(engine.get("scene_assets", []))
        elif engine_name not in {None, "Flame"}:
            runtime_source = str(engine.get("entrypoint") or "lib/game/game.dart")
            runtime_consumer = f"{runtime_source}:update_rules"
            scene_values = list(engine.get("scene_assets", []))
        else:
            runtime_source = "lib/game/game.dart"
            runtime_consumer = "lib/game/game.dart:AuroraGame"
            scene_values = list(engine.get("scene_assets", []))

        # Only use regular, non-empty fixture files for the shipped asset
        # pipeline.  Runtime evidence files stay in .codex-work and are never
        # treated as scene assets.
        candidates = []
        for value in scene_values + [
            "assets/game/final_subject.png",
            "assets/game/final_environment.png",
            "assets/game/final_prop.png",
            "assets/game/final_effect.png",
        ]:
            path = self.root / value
            if value not in candidates and path.is_file() and path.stat().st_size:
                candidates.append(value)
        while len(candidates) < 6:
            extra = f"assets/game/contract_asset_{len(candidates)}.png"
            self.write(extra, b"authored scene fixture")
            candidates.append(extra)
        mode_a_assets = candidates[:3]
        mode_b_assets = candidates[3:6]

        self.write(
            "lib/game/design_contract_page.dart",
            """class DesignContractPage {\n"
            "  static const route = '/play/fixture';\n"
            "  static const layout = 'fixture-layered-hud-v1';\n"
            "}\n""",
        )
        page_capture = ".codex-work/iphone-gameplay-screenshot.png"
        page_capture_path = self.root / page_capture
        evidence = []
        if page_capture_path.is_file() and page_capture_path.stat().st_size:
            evidence.append(
                {
                    "evidence_id": "fixture_page_capture",
                    "acceptance_item": "fixture play page route and layout",
                    "path": page_capture,
                    "type": "screenshot",
                    "project_version": "1.0.0",
                    "bundle_id": "com.example.auroraGame",
                    "device": device,
                    "udid": "00008150-001A114E0C91801E",
                    "status": "Verified",
                    "sha256": hashlib.sha256(page_capture_path.read_bytes()).hexdigest(),
                    "page_id": "fixture_play",
                }
            )
        else:
            # Keep a deterministic record even for negative fixtures; the
            # validator will report the missing file instead of crashing.
            evidence.append(
                {
                    "evidence_id": "fixture_page_capture",
                    "acceptance_item": "fixture play page route and layout",
                    "path": page_capture,
                    "type": "screenshot",
                    "project_version": "1.0.0",
                    "bundle_id": "com.example.auroraGame",
                    "device": device,
                    "udid": "00008150-001A114E0C91801E",
                    "status": "Verified",
                    "sha256": "0" * 64,
                    "page_id": "fixture_play",
                }
            )

        def asset_entry(path, role, geometry, material, layer):
            return {
                "path": path,
                "role": role,
                "geometry": geometry,
                "material": material,
                "render_layer": layer,
                "placeholder": False,
            }

        all_assets = candidates[:6]
        asset_metadata = [
            asset_entry(all_assets[0], "authored environment", "layered raster scene", "textured surface", "background"),
            asset_entry(all_assets[1], "authored gameplay space", "perspective scene mesh", "painted material", "midground"),
            asset_entry(all_assets[2], "authored subject", "beveled sprite silhouette", "painted metal", "foreground"),
            asset_entry(all_assets[3], "authored alternate environment", "layered raster scene", "textured surface", "background"),
            asset_entry(all_assets[4], "authored alternate space", "perspective scene mesh", "fabric and wood", "midground"),
            asset_entry(all_assets[5], "authored alternate actor", "beveled sprite silhouette", "painted material", "foreground"),
        ]

        def mode(mode_id, name, assets, scene):
            return {
                "mode_id": mode_id,
                "name": name,
                "environment": {
                    "value": f"{name} layered environment with weather and depth",
                    "render_consumers": [f"{runtime_consumer}"],
                },
                "road_space": {
                    "value": f"{name} navigable space with perspective lanes",
                    "render_consumers": [f"{runtime_consumer}"],
                },
                "vehicle_or_character": {
                    "value": f"{name} authored actor with material response",
                    "render_consumers": [f"{runtime_consumer}"],
                },
                "entities": {
                    "value": f"{name} interactive entities with occlusion",
                    "render_consumers": [f"{runtime_consumer}"],
                },
                "rules": {
                    "value": f"{name} timing and collision rules drive state changes",
                    "render_consumers": [f"{runtime_consumer}"],
                },
                "results": {
                    "value": f"{name} success and failure feedback with restart",
                    "render_consumers": [f"{runtime_consumer}"],
                },
                "assets": assets,
            }

        contract = {
            "schema_version": 1,
            "project_type": "game",
            "project_identity": {
                "version": "1.0.0",
                "bundle_id": "com.example.auroraGame",
                "device": device,
                "udid": "00008150-001A114E0C91801E",
            },
            "source_of_truth": {
                "id": ".codex-work/game-design-contract.json",
                "version": 1,
                "priority": ["game-design-contract.json", "pages", "domain_render_assets", "evidence", "status"],
                "non_authoritative_sources": [".codex-work/game-engine.json"],
                "conflict_policy": "fail_on_conflict",
            },
            "visual_system": {
                "renderer": "authored layered runtime renderer",
                "projection": f"{visual_mode} orthographic depth projection",
                "coordinate_system": "world x/y with depth z",
                "camera": {"model": "parallax camera with occlusion", "near_clip": 0.1, "far_clip": 100.0},
                "design_tokens": {"depth_unit_px": 24, "shadow_blur_px": 18, "motion_duration_ms": 420},
                "layers": [
                    {"id": "background", "z": 0, "role": "environment"},
                    {"id": "midground", "z": 1, "role": "play space"},
                    {"id": "foreground", "z": 2, "role": "actors and effects"},
                ],
                "materials_lighting": {
                    "materials": ["textured raster", "painted metal", "fabric surface"],
                    "lighting": "directional key light and ambient fill",
                    "shadows": "contact shadows under actors",
                },
                "measurable_thresholds": {
                    "minimum_depth_layers": 3,
                    "minimum_unique_mode_assets": 3,
                    "minimum_motion_duration_ms": 180,
                    "maximum_flat_geometry_ratio": 0,
                    "minimum_occlusion_layers": 2,
                },
                "rejection_thresholds": [
                    "reject fewer than three depth layers or authored scene assets",
                    "reject flat geometry and placeholder assets",
                ],
            },
            "modes": [
                mode("fixture_a", "Aurora Harbor", mode_a_assets, runtime_source),
                mode("fixture_b", "Aurora Market", mode_b_assets, runtime_source),
            ],
            "asset_pipeline": {
                "offline_assets": all_assets,
                "layers": ["background", "midground", "foreground"],
                "transparency": "premultiplied alpha for sprites and effects",
                "occlusion_order": ["background", "midground", "foreground", "effects", "hud"],
                "coordinate_system": "world x/y with depth z",
                "load_entrypoints": [runtime_source],
                "assets": asset_metadata,
                "forbidden": ["placeholder", "flat_rectangle", "static_screenshot"],
            },
            "pages": [
                {
                    "page_id": "fixture_play",
                    "route": "/play/fixture",
                    "route_source": "lib/game/design_contract_page.dart",
                    "layout_signature": "fixture-layered-hud-v1",
                    "composition": "layered scene with diagonal depth and focused HUD",
                    "assets": mode_a_assets[:2],
                    "states": ["loading", "ready", "success", "failure"],
                    "interactions": ["tap actor", "drag camera", "restart run"],
                    "error_recovery": "restore checkpoint and show retry action",
                    "evidence": ["evidence.fixture_page_capture"],
                }
            ],
            "evidence": evidence,
            "status": {
                "plan_status": "Approved",
                "implementation_status": "Implemented",
                "verification_status": "Verified",
                "release_status": "Ready",
            },
            "rejection_rules": [
                "missing independent mode scene",
                "domain field without render consumer",
                "placeholder asset",
                "flat geometry",
                "duplicate evidence",
                "static evidence used for motion",
                "unimplemented route",
                "stale device or build evidence",
            ],
        }
        self.write(".codex-work/game-design-contract.json", json.dumps(contract, indent=2))

    def write_runtime_evidence(self, *, device="iPhone 17 Pro", recording=True,
                               screenshots=True, logs=True, design_contract=True):
        record = {
            "build_id": "aurora-game-build-001",
            "bundle_id": "com.example.auroraGame",
            "device": device,
            "os": "iOS 26.1",
            "recording": ".codex-work/iphone-gameplay-recording.mp4" if recording else "",
            "screenshots": [".codex-work/iphone-gameplay-screenshot.png"] if screenshots else [],
            "logs": [".codex-work/iphone-gameplay.log"] if logs else [],
        }
        self.write(".codex-work/game-runtime.json", json.dumps(record, indent=2))
        if recording:
            self.write(".codex-work/iphone-gameplay-recording.mp4", b"recording")
        if screenshots:
            self.write(".codex-work/iphone-gameplay-screenshot.png", b"screenshot")
        if logs:
            self.write(".codex-work/iphone-gameplay.log", "iPhone gameplay log\n")
        # The playable vertical slice is intentionally separate from the final
        # visual product gate.  Passing fixtures include both contracts.
        self.write("assets/game/final_subject.png", b"authored subject")
        self.write("assets/game/final_environment.png", b"authored environment")
        self.write("assets/game/final_prop.png", b"authored prop")
        self.write("assets/game/final_effect.png", b"authored effect")
        final_evidence = ".codex-work/iphone-gameplay-recording.mp4" if recording else ".codex-work/iphone-gameplay.log"
        final_contract = {
            "schema_version": 1,
            "project_type": "game",
            "claim": "final_visual_product",
            "development_stage": "final_visual_product",
            "prototype_boundary": {"vertical_slice_status": "Passed", "cannot_substitute_for_final": True},
            "common_visual_contract": {
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
                "current_iphone_evidence": [final_evidence],
            },
            "game_visual_contract": {
                "visual_mode": "2.5d",
                "renderer": "authored layered game renderer",
                "camera_model": "depth-aware camera with occlusion",
                "depth_layers": ["background", "midground", "foreground"],
                "materials_lighting": "textured materials and directional lighting",
                "state_variants": "idle active success failure restart",
                "animation_feedback": "subject animation and impact feedback",
                "hud_hierarchy": "goal state score and controls",
                "content_scope": "complete approved game scope",
                "authored_assets": [
                    "assets/game/final_subject.png",
                    "assets/game/final_environment.png",
                    "assets/game/final_prop.png",
                    "assets/game/final_effect.png",
                ],
                "runtime_evidence": [final_evidence],
            },
            "non_game_visual_contract": None,
            "evidence": [".codex-work/game-lobby.json", final_evidence],
        }
        self.write(".codex-work/final-visual-product.json", json.dumps(final_contract, indent=2))
        if design_contract:
            self._write_game_design_contract(device=device)

    def write_flame_fixture(self, *, full=True):
        self.write("assets/game/hero.png", b"hero image")
        self.write("assets/game/scene.png", b"scene image")
        source = """
import 'package:flutter/widgets.dart';
import 'package:flame/game.dart';
import 'package:flame/components.dart';

class AuroraGame extends FlameGame with TapDetector {
  bool won = false;
  bool lost = false;
  @override Future<void> onLoad() async {
    add(SpriteComponent());
    add(ParticleSystemComponent());
  }
  @override void update(double dt) {
    super.update(dt);
    if (won || lost) return;
  }
  @override void onTapDown(TapDownInfo info) { _applyMove(info.eventPosition.game); }
  void _applyMove(Vector2 position) { if (position.x > 0) success(); else failure(); }
  void success() { won = true; add(TextComponent(text: 'Success')); }
  void failure() { lost = true; add(TextComponent(text: 'Failure')); }
  void restart() { won = false; lost = false; children.clear(); }
}

class AuroraGamePage extends StatefulWidget {
  const AuroraGamePage({super.key});
  @override State<AuroraGamePage> createState() => _AuroraGamePageState();
}
class _AuroraGamePageState extends State<AuroraGamePage> with WidgetsBindingObserver {
  final game = AuroraGame();
  @override void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused) game.pauseEngine();
    if (state == AppLifecycleState.resumed) game.resumeEngine();
  }
  @override Widget build(BuildContext context) => GameWidget(
    game: game,
    overlayBuilderMap: {'hud': (_, game) => const Text('Score HUD feedback')},
  );
}
"""
        if not full:
            source = """
import 'package:flutter/material.dart';
class MockGame extends StatelessWidget {
  @override Widget build(BuildContext context) => Container(color: Colors.orange);
}
"""
        self.write("lib/game/game.dart", source)

    def write_godot_fixture(self):
        self.write("assets/game/hero.png", b"hero image")
        self.write("assets/game/scene.png", b"scene image")
        self.write("assets/game/city.png", b"city image")
        self.write("game/project.godot", "[application]\nconfig/name=City\n")
        self.write("game/scenes/city.tscn", "[gd_scene load_steps=2 format=3]\n")
        self.write("game/scripts/city.gd", """
extends Node2D
func _input(event):
    if event is InputEventScreenTouch: apply_move(event.position)
func _process(delta):
    update_rules(delta)
func success(): $HUD.show_success()
func failure(): $HUD.show_failure()
func restart(): get_tree().reload_current_scene()
func pause_game(): get_tree().paused = true
func resume_game(): get_tree().paused = false
""")
        self.write("ios/Runner/game.pck", b"godot pack")
        self.write("ios/Runner/GodotHost.swift", """
import SwiftGodot
import SwiftGodotKit
import Flutter
final class GodotHost: NSObject {
  let channel = FlutterMethodChannel(name: "godot", binaryMessenger: messenger)
  func loadScene() { engine.loadScene("res://scenes/city.tscn") }
  func sendResult(_ result: String) { channel.invokeMethod("gameResult", arguments: result) }
}
""")
        self.write("lib/game/godot_page.dart", """
import 'package:flutter/widgets.dart';
class GodotPage extends StatelessWidget {
  @override Widget build(BuildContext context) => const UiKitView(viewType: 'godot');
  void restart() {}
}
""")

    def test_missing_project_directories_is_reported(self):
        module = self.load_module()
        missing = Path(self.temp.name) / "missing"
        findings = module.validate_project(missing)
        self.assertTrue(any("pubspec.yaml" in item for item in findings))
        self.assertTrue(any("lib/" in item for item in findings))
        self.assertTrue(any("ios/" in item for item in findings))

    def test_missing_engine_manifest_is_reported(self):
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("game-engine.json" in item for item in findings), findings)

    def test_game_project_requires_game_design_contract(self):
        self.write_manifest()
        self.write_flame_fixture()
        self.write_runtime_evidence(design_contract=False)
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("game-design-contract.json" in item for item in findings), findings)

    def test_dependency_without_runtime_import_is_rejected(self):
        self.write_manifest()
        self.write("lib/game/game.dart", "class NotAnEngineGame {}\n")
        self.write_runtime_evidence()
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("Flame" in item and "runtime" in item for item in findings), findings)

    def test_missing_scene_assets_and_evidence_are_rejected(self):
        self.write_manifest()
        self.write("lib/game/game.dart", "import 'package:flame/game.dart'; class MyGame extends FlameGame {}\n")
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("scene asset" in item for item in findings), findings)
        self.assertTrue(any("evidence" in item for item in findings), findings)

    def test_flutter_only_colored_block_mock_is_rejected(self):
        self.write_manifest()
        self.write_flame_fixture(full=False)
        self.write_runtime_evidence()
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("colored-block" in item or "vertical slice" in item for item in findings), findings)

    def test_valid_flame_fixture_passes(self):
        self.write_manifest()
        self.write_flame_fixture()
        self.write_runtime_evidence()
        findings = self.load_module().validate_project(self.root)
        self.assertEqual(findings, [], findings)

    def test_valid_godot_fixture_passes(self):
        self.write_manifest("Godot")
        self.write_godot_fixture()
        self.write_runtime_evidence()
        findings = self.load_module().validate_project(self.root)
        self.assertEqual(findings, [], findings)

    def test_valid_flutter_native_fixture_passes(self):
        self.write_native_manifest()
        self.write_native_fixture()
        self.write_runtime_evidence()
        findings = self.load_module().validate_project(self.root)
        self.assertEqual(findings, [], findings)

    def test_vertical_slice_alone_does_not_pass_final_visual_gate(self):
        self.write_manifest()
        self.write_flame_fixture()
        self.write_runtime_evidence()
        (self.root / ".codex-work" / "final-visual-product.json").unlink()
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("final visual product" in item and "missing" in item for item in findings), findings)

    def test_flutter_native_requires_motion_consumer_and_formula(self):
        self.write_native_manifest()
        self.write_native_fixture(full=False)
        self.write_runtime_evidence()
        findings = self.load_module().validate_project(self.root)
        joined = " ".join(findings).lower()
        self.assertIn("input", joined)
        self.assertIn("rule/update", joined)
        self.assertTrue("animation/effect" in joined or "dynamic" in joined, findings)

    def test_engine_decision_must_be_explicit_and_consistent(self):
        self.write_manifest()
        self.write_flame_fixture()
        self.write_runtime_evidence()
        manifest_path = self.root / ".codex-work/game-engine.json"
        manifest = json.loads(manifest_path.read_text())
        manifest.pop("implementation_mode")
        manifest["engine_required"] = False
        manifest_path.write_text(json.dumps(manifest))
        findings = self.load_module().validate_project(self.root)
        joined = " ".join(findings).lower()
        self.assertIn("implementation_mode", joined)
        self.assertIn("engine_required", joined)

    def test_nested_decision_object_can_select_native_flutter_mode(self):
        self.write_native_manifest()
        self.write_native_fixture()
        self.write_runtime_evidence()
        manifest_path = self.root / ".codex-work/game-engine.json"
        manifest = json.loads(manifest_path.read_text())
        manifest.pop("implementation_mode")
        manifest.pop("engine_required")
        manifest.pop("decision_reason")
        manifest["decision"] = {
            "implementation_mode": "native_flutter",
            "engine_required": False,
            "reason": "Finite turn rules are owned by Flutter.",
        }
        manifest_path.write_text(json.dumps(manifest))
        findings = self.load_module().validate_project(self.root)
        self.assertEqual(findings, [], findings)

    def test_missing_decision_fails_closed_even_with_native_runtime(self):
        self.write_native_manifest()
        self.write_native_fixture()
        self.write_runtime_evidence()
        manifest_path = self.root / ".codex-work/game-engine.json"
        manifest = json.loads(manifest_path.read_text())
        manifest.pop("implementation_mode")
        manifest.pop("engine_required")
        manifest.pop("decision_reason")
        manifest_path.write_text(json.dumps(manifest))
        findings = self.load_module().validate_project(self.root)
        joined = " ".join(findings).lower()
        self.assertIn("implementation_mode", joined)
        self.assertIn("engine_required", joined)
        self.assertIn("decision_reason", joined)

    def test_native_mode_rejects_engine_object(self):
        self.write_native_manifest(engine={"name": "Flame"})
        self.write_native_fixture()
        self.write_runtime_evidence()
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("leave engine absent or null" in item for item in findings), findings)

    def test_paths_must_stay_inside_project_and_scene_assets_cannot_be_work_records(self):
        self.write_manifest(engine={
            "scene_assets": [".codex-work/iphone-gameplay-screenshot.png", "../outside.png"],
            "evidence": ["../outside.mp4"],
        })
        self.write_flame_fixture()
        self.write_runtime_evidence()
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("scene asset" in item and ".codex-work" in item for item in findings), findings)
        self.assertTrue(any("inside project" in item or "project-relative" in item for item in findings), findings)

    def test_vertical_slice_and_runtime_record_are_required(self):
        self.write_manifest()
        self.write("assets/game/hero.png", b"hero")
        self.write("assets/game/scene.png", b"scene")
        self.write("lib/game/game.dart", """
import 'package:flame/game.dart';
import 'package:flame/game_widget.dart';
class MyGame extends FlameGame { @override void update(double dt) {} }
""")
        self.write_runtime_evidence(recording=False, screenshots=False, logs=False)
        findings = self.load_module().validate_project(self.root)
        joined = " ".join(findings).lower()
        self.assertIn("input", joined)
        self.assertIn("success", joined)
        self.assertIn("restart", joined)
        self.assertIn("lifecycle", joined)
        self.assertTrue(any("recording" in item for item in findings), findings)

    def test_game_requires_explicit_25d_or_3d_visual_mode(self):
        self.write_manifest()
        self.write_flame_fixture()
        self.write_runtime_evidence()
        manifest_path = self.root / ".codex-work/game-engine.json"
        manifest = json.loads(manifest_path.read_text())
        manifest.pop("visual_mode")
        manifest_path.write_text(json.dumps(manifest, indent=2))
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("visual_mode" in item for item in findings), findings)

    def test_game_requires_immersive_game_lobby_contract(self):
        self.write_manifest()
        self.write_flame_fixture()
        self.write_runtime_evidence()
        manifest_path = self.root / ".codex-work/game-engine.json"
        manifest = json.loads(manifest_path.read_text())
        manifest.pop("game_lobby")
        manifest_path.write_text(json.dumps(manifest, indent=2))
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("game_lobby" in item for item in findings), findings)

    def test_game_lobby_rejects_standard_welcome_actions(self):
        self.write_manifest()
        self.write_flame_fixture()
        self.write_runtime_evidence()
        manifest_path = self.root / ".codex-work/game-engine.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["game_lobby"]["primary_actions"] = ["Continue"]
        manifest_path.write_text(json.dumps(manifest, indent=2))
        findings = self.load_module().validate_project(self.root)
        self.assertTrue(any("primary_actions" in item for item in findings), findings)

    def test_unknown_engine_uses_declared_generic_runtime_contract(self):
        self.write_manifest("Defold", visual_mode="3d", visual_contract={
            "renderer": "Defold iOS renderer",
            "camera_model": "perspective camera",
            "depth_layers": ["background", "midground", "foreground"],
            "materials_lighting": "PBR materials, directional lighting and contact shadows",
            "authored_assets": ["assets/game/hero.png", "assets/game/scene.png"],
            "animation_feedback": "state-driven animation and particles",
            "no_flat_color_blocks": True,
        })
        self.write("assets/game/hero.png", b"hero image")
        self.write("assets/game/scene.png", b"scene image")
        self.write("lib/game/game.defold", """
camera = PerspectiveCamera.new()
scene = Scene3D.new()
background = MeshInstance3D.new()
midground = MeshInstance3D.new()
foreground = MeshInstance3D.new()
hero = TexturedModel.new(material='PBR', shadow=True)
function on_input(event) update_rules(event)
function update_rules(dt) animate_particles(dt)
function success() show_result('Success')
function failure() show_result('Failure')
function restart() reset_scene()
function pause_game() stop_runtime()
function resume_game() start_runtime()
""")
        manifest_path = self.root / ".codex-work/game-engine.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["engine"].update({
            "entrypoint": "lib/game/game.defold",
            "scene_assets": ["assets/game/hero.png", "assets/game/scene.png"],
            "runtime_markers": ["PerspectiveCamera", "MeshInstance3D", "TexturedModel", "animate_particles"],
            "native_bridge": "Defold iOS host adapter",
        })
        manifest_path.write_text(json.dumps(manifest, indent=2))
        self.write_runtime_evidence()
        findings = self.load_module().validate_project(self.root)
        self.assertEqual(findings, [], findings)


if __name__ == "__main__":
    unittest.main()
