import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_visual_implementation.py"
SPEC = importlib.util.spec_from_file_location("visual_contract", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VisualImplementationContractTests(unittest.TestCase):
    def add_design_system_contract(self, root, ledger, *, kind="awesome-design-md", status="Verified"):
        (root / "DESIGN.md").write_text(
            "# Product design\nSource: awesome-design-md Apple DESIGN.md\n",
            encoding="utf-8",
        )
        master = root / "design-system/product/MASTER.md"
        master.parent.mkdir(parents=True, exist_ok=True)
        master.write_text(
            "# Master\nTypography, spacing, safe area, motion and component rules.\n",
            encoding="utf-8",
        )
        review = root / ".codex-work/ui-ux-review.md"
        review.parent.mkdir(parents=True, exist_ok=True)
        review.write_text(
            "# UI/UX review\nReference: awesome-design-md Apple DESIGN.md\n"
            "Reviewed with ui-ux-pro-max for Flutter/iPhone.\n",
            encoding="utf-8",
        )
        categories = {}
        for category in MODULE.DESIGN_REVIEW_CATEGORIES:
            categories[category] = {
                "status": status,
                "finding": f"{category} reviewed against the current iPhone surface.",
                "resolution": f"{category} resolved in the implementation contract.",
                "evidence": [".codex-work/ui-ux.png"],
            }
        ledger["design_system"] = {
            "reference": {
                "kind": kind,
                "name": "Apple-inspired mobile reference" if kind == "awesome-design-md" else "Project custom design system",
                "source": "awesome-design-md/references/design-md/apple/DESIGN.md" if kind == "awesome-design-md" else "project brief",
                "selection_reason": "The reference fits bright iPhone product surfaces and image-led hierarchy.",
            },
            "design_doc": "DESIGN.md",
            "master": "design-system/product/MASTER.md",
            "ui_ux_command": "python3 ui-ux-pro-max/scripts/search.py mobile productivity --design-system --stack flutter",
            "ui_ux_query": "mobile productivity bright immersive",
            "ui_ux_stack": "flutter",
            "status": status,
            "component_selection_gate": "design_review_verified",
            "ui_ux_review": {
                "record": ".codex-work/ui-ux-review.md",
                "status": status,
                "unresolved_findings": [] if status == "Verified" else ["unfinished review"],
                "categories": categories,
                "current_iphone_evidence": [".codex-work/ui-ux.png"],
            },
        }
        (root / ".codex-work/ui-ux.png").write_bytes(b"ui-ux-evidence")

    def procedural_ledger(self, root, kind="flutter"):
        source = "lib/page_module/home_page.dart" if kind == "flutter" else "aduit/site/PrivacyPolicy.html"
        page = root / source
        page.parent.mkdir(parents=True)
        implementation = "lib/common_module/motion/home_bg.dart" if kind == "flutter" else source
        renderer = root / implementation
        renderer.parent.mkdir(parents=True, exist_ok=True)
        if kind == "flutter":
            page.write_text("class HomePage { final background = HomeBg(); }")
            renderer.write_text("class HomeBg extends CustomPainter { void paint(Canvas canvas, Size size) {} }")
        else:
            page.write_text("<canvas id='bg'></canvas><script>function drawScene() {} drawScene();</script>")
        image = root / "assets/backgrounds/home/home_background.png"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"home-background-fixture")
        page.write_text(page.read_text() + "\n'home_background.png'")
        evidence = root / ".codex-work"
        evidence.mkdir()
        (evidence / "screen.png").write_bytes(b"screen-fixture")
        (evidence / "motion.mov").write_bytes(b"recording-fixture")
        background = {
            "mode": "procedural", "scene_id": "home_atmos",
            "entrypoint": "HomeBg" if kind == "flutter" else "drawScene",
            "implementation": [implementation], "recording": ".codex-work/motion.mov",
            "asset": "assets/backgrounds/home/home_background.png",
            "opacity": 0.12, "placement": "upper-right behind content",
            "gradient_tokens": ["brandGradient", "sunsetGradient"],
            "palette_hex": ["#F05A3C", "#FFB347", "#D84315"],
        }
        ledger = {
            "project_type": "game",
            "build": {"id": "1", "device": "iPhone 17 Pro", "os": "iOS 26.5"},
            "layout_history": {"scope": "first_record", "records": []},
            "surfaces": [{"id": "home", "kind": kind, "source": source,
                          "layout": self.layout_record(), "background": background}],
            "checks": [{"id": gate, "status": "Verified", "targets": ["home"],
                        "implementation": [source], "evidence": [".codex-work/motion.mov"],
                        "result": "Observed on current build; fixture does not certify visual quality."}
                       for gate in MODULE.VISUAL_GATES],
        }
        self.add_design_system_contract(root, ledger)
        return ledger

    def test_procedural_background_keeps_image_accent_alongside_scene(self):
        for kind in ("flutter", "html"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ledger = self.procedural_ledger(root, kind)
                (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
                self.assertTrue((root / ledger["surfaces"][0]["background"]["asset"]).is_file())
                self.assertEqual(MODULE.validate_visual_ledger(root), [])

    def test_non_game_requires_real_ui_component_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            ledger["project_type"] = "non_game"
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
            findings = MODULE.validate_visual_ledger(root)
            self.assertTrue(any("ui_component_contract" in item for item in findings), findings)

    def test_non_game_rejects_flat_visual_treatment_and_unused_component(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            ledger["project_type"] = "non_game"
            ledger["ui_component_contract"] = {
                "components": [{
                    "name": "flutter_animate",
                    "version": "4.5.0",
                    "license/source": "pub.dev",
                    "actual_consumer": "lib/page_module/home_page.dart",
                    "runtime_markers": ["flutter_animate"],
                }],
                "visual_constraints": {
                    "no_simple_line_art": True,
                    "no_flat_color_blocks": True,
                    "no_solid_color_background": True,
                },
                "runtime_evidence": [".codex-work/motion.mov"],
            }
            ledger["surfaces"][0]["background"]["visual_treatment"] = "solid color background"
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
            findings = MODULE.validate_visual_ledger(root)
            self.assertTrue(any("at least two" in item for item in findings), findings)
            self.assertTrue(any("flat/simple" in item or "solid color" in item for item in findings), findings)

    def test_non_game_accepts_two_real_ui_components_and_rich_background_treatment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            ledger["project_type"] = "non_game"
            page = root / ledger["surfaces"][0]["source"]
            page.write_text(page.read_text() + " flutter_animate BackdropFilter", encoding="utf-8")
            ledger["surfaces"][0]["background"]["visual_treatment"] = (
                "textured translucent scene with material, directional light and depth"
            )
            ledger["ui_component_contract"] = {
                "components": [
                    {
                        "name": "flutter_animate",
                        "version": "4.5.0",
                        "license/source": "pub.dev",
                        "actual_consumer": "lib/page_module/home_page.dart",
                        "runtime_markers": ["flutter_animate"],
                    },
                    {
                        "name": "BackdropFilter",
                        "version": "Flutter SDK",
                        "license/source": "Flutter SDK",
                        "actual_consumer": "lib/page_module/home_page.dart",
                        "runtime_markers": ["BackdropFilter"],
                    },
                ],
                "visual_constraints": {
                    "no_simple_line_art": True,
                    "no_flat_color_blocks": True,
                    "no_solid_color_background": True,
                },
                "runtime_evidence": [".codex-work/motion.mov"],
            }
            self.add_design_system_contract(root, ledger)
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
            self.assertEqual(MODULE.validate_visual_ledger(root), [])

    def test_non_game_requires_verified_design_system_before_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            ledger["project_type"] = "non_game"
            self.add_design_system_contract(root, ledger, status="Draft")
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
            findings = MODULE.validate_visual_ledger(root)
            self.assertTrue(any("design_system.status must be Verified" in item for item in findings), findings)
            self.assertTrue(any("ui_ux_review.status must be Verified" in item for item in findings), findings)

    def test_game_visual_ledger_also_requires_design_system(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            ledger["project_type"] = "game"
            ledger.pop("design_system", None)
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
            findings = MODULE.validate_visual_ledger(root)
            self.assertTrue(any("design_system contract is required" in item for item in findings), findings)

    def test_visual_ledger_requires_explicit_project_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            ledger.pop("project_type", None)
            ledger.pop("design_system", None)
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
            findings = MODULE.validate_visual_ledger(root)
            self.assertTrue(any("project_type is required" in item for item in findings), findings)
            self.assertTrue(any("design_system contract is required" in item for item in findings), findings)

    def test_non_game_requires_design_artifacts_inside_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            ledger["project_type"] = "non_game"
            ledger["design_system"] = {
                "reference": {"kind": "custom", "name": "Custom", "source": "brief", "selection_reason": "fit"},
                "design_doc": "/tmp/DESIGN.md",
                "master": "design-system/product/MASTER.md",
                "ui_ux_stack": "flutter",
                "status": "Verified",
            }
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
            findings = MODULE.validate_visual_ledger(root)
            self.assertTrue(any("design_doc must stay inside" in item for item in findings), findings)
            self.assertTrue(any("ui_ux_command" in item for item in findings), findings)

    def test_every_background_mode_requires_a_translucent_image(self):
        for mode in ("image", "procedural", "animation", "hybrid"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ledger = self.procedural_ledger(root)
                background = ledger["surfaces"][0]["background"]
                background.update(mode=mode, opacity=0.12, placement="upper-right behind content")
                background.pop("asset", None)
                (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
                self.assertIn("home: missing required translucent background image asset",
                              MODULE.validate_visual_ledger(root))

    def test_translucent_image_rejects_invisible_opaque_or_unplaced_records(self):
        for field, value in (("opacity", None), ("opacity", 0), ("opacity", 1),
                             ("opacity", -0.1), ("opacity", 1.1), ("opacity", True),
                             ("opacity", "0.12"), ("opacity", float("nan")),
                             ("placement", None), ("placement", ""), ("placement", " ")):
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ledger = self.procedural_ledger(root)
                background = ledger["surfaces"][0]["background"]
                image = root / "assets/backgrounds/home/home_background.png"
                image.parent.mkdir(parents=True, exist_ok=True)
                image.write_bytes(b"background-fixture")
                background.update(mode="image", asset=str(image.relative_to(root)),
                                  opacity=0.12, placement="upper-right behind content")
                source = root / ledger["surfaces"][0]["source"]
                source.write_text(source.read_text() + " const bg = 'home_background.png';")
                if value is None:
                    background.pop(field)
                else:
                    background[field] = value
                (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
                self.assertTrue(any(f"background {field}" in finding
                                    for finding in MODULE.validate_visual_ledger(root)))

    def test_scene_cannot_replace_missing_or_unreferenced_image_accent(self):
        for fault in ("missing_file", "unused", "wrong_page"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ledger = self.procedural_ledger(root)
                surface = ledger["surfaces"][0]
                if fault == "missing_file":
                    (root / surface["background"]["asset"]).unlink()
                    expected = "missing or empty file"
                elif fault == "unused":
                    (root / surface["source"]).write_text("class HomePage { final bg = HomeBg(); }")
                    expected = "source does not reference its background asset"
                else:
                    original = root / surface["background"]["asset"]
                    other = root / "assets/backgrounds/other/other_background.png"
                    other.parent.mkdir(parents=True)
                    original.rename(other)
                    surface["background"]["asset"] = str(other.relative_to(root))
                    expected = "background asset must be page-specific"
                (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
                self.assertTrue(any(expected in item for item in MODULE.validate_visual_ledger(root)))

    def test_gradient_metadata_is_required_but_does_not_certify_visual_quality(self):
        cases = (([], []), ([], ["#000000"]), ([], ["#0B234A", "#808080"]),
                 (["customGradient"], ["#FFFFFF"]), (None, None))
        for tokens, colors in cases:
            with self.subTest(tokens=tokens, colors=colors), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ledger = self.procedural_ledger(root)
                background = ledger["surfaces"][0]["background"]
                for key, value in (("gradient_tokens", tokens), ("palette_hex", colors)):
                    if value is None:
                        background.pop(key)
                    else:
                        background[key] = value
                (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
                findings = MODULE.validate_visual_ledger(root)
                if tokens:
                    self.assertEqual(findings, [], findings)
                else:
                    self.assertTrue(any("gradient_tokens must list at least one" in item for item in findings), findings)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            ledger["checks"] = [
                dict(row, exclusions={"home": "Theme does not use gradients"})
                if row["id"] == "gradients" else row
                for row in ledger["checks"]
            ]
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
            self.assertTrue(any("hard requirement cannot be excluded" in item
                                for item in MODULE.validate_visual_ledger(root)))

    def test_distinct_pages_may_share_the_same_palette(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            second = dict(ledger["surfaces"][0], id="task", source="lib/page_module/task_page.dart",
                          layout=self.layout_record(1))
            second["background"] = dict(second["background"], scene_id="task_scene")
            second["background"]["asset"] = "assets/backgrounds/task/task_background.png"
            image = root / second["background"]["asset"]
            image.parent.mkdir(parents=True)
            image.write_bytes(b"distinct-task-background-fixture")
            (root / second["source"]).write_text("class TaskPage { final background = HomeBg(); } 'task_background.png'")
            ledger["surfaces"].append(second)
            for check in ledger["checks"]:
                check["targets"].append("task")
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
            self.assertEqual(MODULE.validate_visual_ledger(root), [])

    def test_optional_color_metadata_rejects_malformed_values(self):
        for key, value in (("gradient_tokens", "token"), ("gradient_tokens", [None]),
                           ("gradient_tokens", [["token"]]), ("palette_hex", "#FFFFFF"),
                           ("palette_hex", [123]), ("palette_hex", ["not-a-color"]),
                           ("palette_hex", ["#1234567"])):
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ledger = self.procedural_ledger(root)
                ledger["surfaces"][0]["background"][key] = value
                (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
                self.assertTrue(any(key in item for item in MODULE.validate_visual_ledger(root)))

    def test_solid_color_typography_does_not_require_gradient_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            theme = root / "lib/common_module/theme/app_theme.dart"
            theme.parent.mkdir(parents=True)
            theme.write_text("final display = TextStyle(fontStyle: FontStyle.italic); "
                             "final heading = TextStyle(fontWeight: FontWeight.w700); "
                             "final body = TextStyle(); final metadata = TextStyle(); final action = TextStyle();")
            pages = root / "lib/page_module"
            pages.mkdir()
            for name in ("home", "task", "settings"):
                (pages / f"{name}_page.dart").write_text("final title = AppTheme.heading; final copy = Text.rich(TextSpan());")
            findings = MODULE.validate(root)
            self.assertFalse(any("gradient" in item.lower() for item in findings), findings)
            self.assertFalse(any("typography implementation" in item for item in findings), findings)

    def test_hybrid_background_retains_image_and_animation_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            background = ledger["surfaces"][0]["background"]
            background.update(mode="hybrid", asset="assets/backgrounds/home/home_background.png")
            image = root / background["asset"]
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes(b"image-fixture")
            page = root / ledger["surfaces"][0]["source"]
            page.write_text(page.read_text() + " const texture = 'home_background.png';")
            ledger_path = root / ".codex-work/ui-visual-gates.json"
            ledger_path.write_text(json.dumps(ledger))
            self.assertEqual(MODULE.validate_visual_ledger(root), [])
            image.unlink()
            self.assertTrue(any("missing or empty file" in item for item in MODULE.validate_visual_ledger(root)))

    def test_component_and_generated_animation_backgrounds_use_local_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            resource = root / "assets/media/anim/home/scene.riv"
            resource.parent.mkdir(parents=True)
            resource.write_bytes(b"local-animation-fixture")
            background = ledger["surfaces"][0]["background"]
            background.update(mode="animation", resources=["assets/media/anim/home/scene.riv"])
            ledger_path = root / ".codex-work/ui-visual-gates.json"
            ledger_path.write_text(json.dumps(ledger))
            self.assertEqual(MODULE.validate_visual_ledger(root), [])
            for resources, expected in (
                (["https://example.com/bg.riv"], "missing or empty file"),
                (["assets/missing.riv"], "missing or empty file"),
                ([".codex-work/screen.png"], "bundled project assets"),
                ("assets/media/anim/home/scene.riv", "must be a list"),
            ):
                with self.subTest(resources=resources):
                    background["resources"] = resources
                    ledger_path.write_text(json.dumps(ledger))
                    self.assertTrue(any(expected in item for item in MODULE.validate_visual_ledger(root)))

    def test_procedural_background_rejects_unwired_or_unverified_scene(self):
        cases = (
            ({"mode": "unknown"}, "unknown background mode"),
            ({"mode": []}, "unknown background mode"),
            ({"mode": None}, "unknown background mode"),
            ({"scene_id": ""}, "scene_id"),
            ({"implementation": []}, "implementation"),
            ({"implementation": ["../outside.dart"]}, "inside project"),
            ({"implementation": [".codex-work/screen.png"]}, "executable background implementation"),
            ({"implementation": ["lib/missing.dart"]}, "missing or empty file"),
            ({"entrypoint": "UnusedBg"}, "entrypoint"),
            ({"recording": ".codex-work/screen.png"}, "motion recording"),
            ({"recording": ".codex-work/missing.mov"}, "missing or empty file"),
            ({"asset": "unused.png"}, "missing or empty file"),
        )
        for changes, expected in cases:
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ledger = self.procedural_ledger(root)
                ledger["surfaces"][0]["background"].update(changes)
                (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
                self.assertTrue(any(expected in item for item in MODULE.validate_visual_ledger(root)))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            (root / "lib/common_module/motion/home_bg.dart").write_text("class OtherBg {}")
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps(ledger))
            self.assertTrue(any("entrypoint" in item for item in MODULE.validate_visual_ledger(root)))

    def test_procedural_background_rejects_scene_reuse_and_native_animation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self.procedural_ledger(root)
            second = dict(ledger["surfaces"][0], id="task", layout=self.layout_record(1))
            second["background"] = dict(second["background"], gradient_tokens=["taskGrad", "taskAccent"])
            ledger["surfaces"].append(second)
            ledger_path = root / ".codex-work/ui-visual-gates.json"
            ledger_path.write_text(json.dumps(ledger))
            self.assertTrue(any("scene_id is reused" in item for item in MODULE.validate_visual_ledger(root)))
            ledger["surfaces"] = [dict(ledger["surfaces"][0], kind="native")]
            ledger_path.write_text(json.dumps(ledger))
            self.assertTrue(any("native Launch Screen must stay static" in item
                                for item in MODULE.validate_visual_ledger(root)))

    def layout_record(self, variant=0):
        if variant == 0:
            return {
                "composition": "editorial_split", "region_order": ["summary", "feature", "collection"],
                "media_structure": "inset_landscape", "content_structure": "chapter_rails",
                "action_structure": "inline_contextual", "navigation_structure": "section_index",
            }
        return {
            "composition": "layered_task_canvas", "region_order": ["workspace", "result", "controls"],
            "media_structure": "annotated_subject", "content_structure": "process_stages",
            "action_structure": "docked_tools", "navigation_structure": "contextual_return",
        }

    def test_layout_records_require_structural_dimensions(self):
        findings = MODULE.validate_layout_diversity([{"id": "home", "kind": "flutter"}])
        self.assertTrue(any("layout record" in item for item in findings))

    def test_layout_rejects_reskins_and_minor_structural_changes(self):
        first = {"id": "home", "kind": "flutter", "layout": self.layout_record()}
        second = {"id": "explore", "kind": "flutter", "layout": dict(self.layout_record(),
                  composition="  EDITORIAL-SPLIT  ", color="orange", title="Different")}
        self.assertTrue(any("insufficient structural difference" in item
                            for item in MODULE.validate_layout_diversity([first, second])))
        second["layout"]["composition"] = "masonry_gallery"
        second["layout"]["media_structure"] = "portrait_tiles"
        self.assertTrue(MODULE.validate_layout_diversity([first, second]))

    def test_layout_accepts_distinct_pages_and_checks_previous_projects(self):
        surfaces = [{"id": "home", "kind": "flutter", "layout": self.layout_record()},
                    {"id": "task", "kind": "flutter", "layout": self.layout_record(1)}]
        self.assertEqual(MODULE.validate_layout_diversity(surfaces), [])
        history = [{"project": "previous-project", "id": "previous-home", "layout": self.layout_record()}]
        self.assertTrue(any("previous-project" in item
                            for item in MODULE.validate_layout_diversity(surfaces, history)))

    def test_only_same_surface_representations_can_share_layout(self):
        surfaces = [
            {"id": "welcome", "kind": "flutter", "source": "lib/welcome.dart", "layout": self.layout_record()},
            {"id": "welcome_html", "kind": "html", "source": "aduit/welcome.html",
             "same_layout_as": "welcome", "layout": self.layout_record()},
        ]
        self.assertEqual(MODULE.validate_layout_diversity(surfaces), [])
        surfaces[1].update(id="entry", kind="flutter", source="lib/page_module/entry/entry_page.dart")
        self.assertTrue(any("invalid same_layout_as" in item
                            for item in MODULE.validate_layout_diversity(surfaces)))

    def test_layout_rejects_malformed_values_and_unknown_aliases(self):
        for bad in ({"region_order": []}, {"composition": []}, {"region_order": [False]},
                    {"composition": ""}):
            with self.subTest(bad=bad):
                self.assertTrue(MODULE.validate_layout_diversity([
                    {"id": "home", "kind": "flutter", "layout": dict(self.layout_record(), **bad)}]))
        self.assertTrue(MODULE.validate_layout_diversity([
            {"id": "x", "kind": "html", "source": "aduit/welcome.html",
             "same_layout_as": "missing", "layout": self.layout_record()}]))

    def test_dart_welcome_and_delivery_only_html_are_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lib").mkdir()
            welcome = root / "lib/welcome.dart"
            welcome.write_text("class WelcomePage extends StatelessWidget { final cards = PageView(); }", encoding="utf-8")
            (root / "aduit").mkdir()
            (root / "aduit/welcome.html").write_text("<html>Standalone delivery</html>", encoding="utf-8")
            (root / "lib/policy_page.dart").write_text(
                "class PolicyPage { final view = WebViewWidget(); "
                "final rawUrl = 'https://example.invalid/aduit/PrivacyPolicy.html'; }", encoding="utf-8"
            )
            self.assertEqual(MODULE.validate_welcome_source(root), [])
            self.assertIn(welcome, MODULE.page_files([welcome]))

    def test_welcome_migration_rejects_wrappers_scrollers_and_stale_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lib").mkdir()
            welcome = root / "lib/welcome.dart"
            self.assertTrue(MODULE.validate_welcome_source(root))
            for token in ("WebViewWidget()", "HtmlWidget()", "AppBridge", "SingleChildScrollView()", "ListView()"):
                with self.subTest(token=token):
                    welcome.write_text("class WelcomePage {} " + token, encoding="utf-8")
                    self.assertTrue(MODULE.validate_welcome_source(root))
            welcome.write_text("class WelcomePage {}", encoding="utf-8")
            pubspec = root / "pubspec.yaml"
            pubspec.write_text("flutter: {assets: [aduit/welcome.html]}", encoding="utf-8")
            self.assertTrue(any("runtime source" in item for item in MODULE.validate_welcome_source(root)))
            pubspec.unlink()
            legacy = root / "welcome.html"
            legacy.write_text("old", encoding="utf-8")
            self.assertTrue(any("obsolete Welcome" in item for item in MODULE.validate_welcome_source(root)))

    def test_welcome_is_a_required_visual_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lib").mkdir()
            (root / "lib/welcome.dart").write_text("class WelcomePage {}", encoding="utf-8")
            (root / ".codex-work").mkdir()
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps({"build": {"id": "1", "device": "iPhone 17 Pro Max", "os": "iOS 26.5"}, "surfaces": [], "checks": []}), encoding="utf-8")
            self.assertIn("visual surface is not inventoried: lib/welcome.dart", MODULE.validate_visual_ledger(root))

    def test_alternative_theme_directory_cannot_replace_fixed_brand_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            theme = root / "lib/theme"
            theme.mkdir(parents=True)
            (theme / "app_theme.dart").write_text("final brandGradient = LinearGradient();", encoding="utf-8")
            findings = MODULE.validate(root)
            self.assertTrue(any("lib/common_module/theme/app_theme.dart" in item for item in findings))

    def test_missing_implementation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lib").mkdir()
            (root / "lib/main.dart").write_text("void main() {}", encoding="utf-8")
            findings = MODULE.validate(root)
            self.assertTrue(any("AnimationController" in item for item in findings))
            self.assertTrue(any("ui-refinement" in item for item in findings))

    def test_complete_contract_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            theme = root / "lib/common_module/theme"
            pages = root / "lib/page_module"
            theme.mkdir(parents=True)
            pages.mkdir(parents=True)
            (theme / "app_theme.dart").write_text(
                """
                final display = TextStyle(fontStyle: FontStyle.italic);
                final heading = TextStyle(fontWeight: FontWeight.w700);
                final body = TextStyle(); final metadata = TextStyle(); final action = TextStyle();
                final brandGradient = LinearGradient();
                """,
                encoding="utf-8",
            )
            shared = """
            class Particles extends CustomPainter { final position; final velocity; final gravity; final color; final trail; }
            class Controller { AnimationController controller; }
            void tap(TapUpDetails details) { onTapUp(details); }
            final gradient = LinearGradient(); final mask = ShaderMask();
            final rich = Text.rich(TextSpan()); final reduce = disableAnimations;
            """
            for name in ("home_page.dart", "task_page.dart", "settings_page.dart"):
                (pages / name).write_text(shared, encoding="utf-8")
            evidence = root / ".codex-work"
            evidence.mkdir()
            (evidence / "ui-refinement.md").write_text(
                "Round 1 iPhone: a.png\nRound 2 iPhone: b.png\nRound 3 iPhone: c.png",
                encoding="utf-8",
            )
            (evidence / "particle-evidence.md").write_text(
                "Action one: before/active/result.\nAction two: before/active/result.",
                encoding="utf-8",
            )
            # A few styling tokens and evidence headings cannot satisfy the full
            # visual contract: the per-surface acceptance ledger is still absent.
            self.assertTrue(any("ui-visual-gates.json" in item for item in MODULE.validate(root)))

    def test_full_visual_ledger_validates_coverage_and_real_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lib/page_module").mkdir(parents=True)
            (root / "lib/page_module/home_page.dart").write_text(
                "class HomePage {}\nconst backgroundAsset = 'home_background.png';", encoding="utf-8"
            )
            evidence = root / ".codex-work"
            evidence.mkdir()
            (evidence / "home.png").write_bytes(b"runtime-evidence-fixture")
            (evidence / "motion.mov").write_bytes(b"runtime-recording-fixture")
            background = root / "assets/backgrounds/home/home_background.png"
            background.parent.mkdir(parents=True)
            background.write_bytes(b"background-fixture")
            (evidence / "ui-visual-gates.json").write_text(json.dumps({
                "project_type": "game",
                "build": {"id": "1.0.0+1", "device": "iPhone 17 Pro Max", "os": "iOS 26.5"},
                "layout_history": {"scope": "first_record", "records": []},
                "surfaces": [{"id": "home", "kind": "flutter", "source": "lib/page_module/home_page.dart",
                              "layout": self.layout_record(),
                              "background": {"asset": "assets/backgrounds/home/home_background.png",
                                             "opacity": 0.12, "placement": "upper-right behind content",
                                             "gradient_tokens": ["brandGradient", "sunsetGradient"],
                                             "palette_hex": ["#F05A3C", "#FFB347", "#6F2DBD"]}}],
                "checks": [{"id": gate, "status": "Verified", "targets": ["home"],
                            "implementation": ["lib/page_module/home_page.dart"],
                            "evidence": [".codex-work/motion.mov" if gate in {"page_transitions", "background_motion"}
                                         else ".codex-work/home.png"],
                            "result": "Observed on the recorded build."}
                           for gate in ("brand_palette", "gradients", "typography", "particles", "motion",
                                        "page_transitions", "background_motion",
                                        "backgrounds", "decoration", "icons", "emoji", "text_density", "media", "content", "layout", "controls", "states",
                                        "appearance", "accessibility", "launch_flow", "app_icon", "html", "refinement")]
            }), encoding="utf-8")
            ledger = json.loads((evidence / "ui-visual-gates.json").read_text())
            self.add_design_system_contract(root, ledger)
            (evidence / "ui-visual-gates.json").write_text(json.dumps(ledger), encoding="utf-8")
            self.assertEqual(MODULE.validate_visual_ledger(root), [])

            ledger_path = evidence / "ui-visual-gates.json"
            ledger = json.loads(ledger_path.read_text())
            for history, expected in (
                (None, "missing layout_history"),
                ({"scope": [], "records": []}, "missing layout_history"),
                ({"scope": "available_records", "records": []}, "must contain records"),
                ({"scope": "unavailable", "records": []}, "not verified"),
                ({"scope": "first_record", "records": [{}]}, "cannot contain prior records"),
            ):
                with self.subTest(layout_history=history):
                    ledger_path.write_text(json.dumps(dict(ledger, layout_history=history)))
                    self.assertTrue(any(expected in item for item in MODULE.validate_visual_ledger(root)))
            for gate in ("decoration", "icons", "emoji", "text_density", "page_transitions", "background_motion"):
                with self.subTest(missing_gate=gate):
                    incomplete = dict(ledger, checks=[row for row in ledger["checks"] if row["id"] != gate])
                    ledger_path.write_text(json.dumps(incomplete))
                    self.assertIn(f"missing visual gate: {gate}", MODULE.validate_visual_ledger(root))
            for gate in ("icons", "emoji", "text_density"):
                with self.subTest(uncovered_gate=gate):
                    incomplete = dict(ledger, checks=[dict(row, targets=[]) if row["id"] == gate else row
                                                    for row in ledger["checks"]])
                    ledger_path.write_text(json.dumps(incomplete))
                    self.assertIn(f"{gate}: surface has no acceptance result: home", MODULE.validate_visual_ledger(root))

            for gate in ("page_transitions", "background_motion"):
                with self.subTest(uncovered_flutter_motion=gate):
                    incomplete = dict(ledger, checks=[dict(row, targets=[], exclusions={"home": "Focused page"})
                                                     if row["id"] == gate else row for row in ledger["checks"]])
                    ledger_path.write_text(json.dumps(incomplete))
                    self.assertIn(f"{gate}: Flutter surface has no motion acceptance result: home",
                                  MODULE.validate_visual_ledger(root))
                with self.subTest(still_image_cannot_prove_motion=gate):
                    incomplete = dict(ledger, checks=[dict(row, evidence=[".codex-work/home.png"])
                                                     if row["id"] == gate else row for row in ledger["checks"]])
                    ledger_path.write_text(json.dumps(incomplete))
                    self.assertIn(f"{gate}: needs an iPhone motion recording file",
                                  MODULE.validate_visual_ledger(root))

            # The independent HTML is a second representation of the same
            # Welcome UI, not a different runtime page requiring another image.
            welcome_background = root / "assets/backgrounds/welcome/welcome_background.png"
            welcome_background.parent.mkdir(parents=True)
            welcome_background.write_bytes(b"distinct-welcome-background")
            (root / "lib/welcome.dart").write_text(
                "class WelcomePage {} const bg = 'welcome_background.png';", encoding="utf-8"
            )
            (root / "aduit").mkdir()
            (root / "aduit/welcome.html").write_text(
                '<img src="data:image/png;base64,aGVsbG8=">', encoding="utf-8"
            )
            for kind, surface_id, source in (("html", "welcome_html", "aduit/welcome.html"),
                                             ("flutter", "welcome", "lib/welcome.dart")):
                ledger["surfaces"].append({
                    "id": surface_id, "kind": kind, "source": source,
                    "layout": self.layout_record(1),
                    **({"same_layout_as": "welcome"} if kind == "html" else {}),
                    "background": {
                        "asset": "assets/backgrounds/welcome/welcome_background.png",
                        "opacity": 0.15, "placement": "right edge behind introduction",
                        "gradient_tokens": ["welcomeGradient", "accentGradient"],
                        "palette_hex": ["#F05A3C", "#FFB347", "#6F2DBD"],
                    },
                })
                for row in ledger["checks"]:
                    row["targets"].append(surface_id)
            ledger_path.write_text(json.dumps(ledger))
            self.assertEqual(MODULE.validate_visual_ledger(root), [])

            # Delivery-only HTML has separate motion rules; the two Flutter
            # gates must cover every runtime Flutter page, without waivers.
            flutter_only = dict(ledger, checks=[
                dict(row, targets=[target for target in row["targets"] if target != "welcome_html"])
                if row["id"] in {"page_transitions", "background_motion"} else row
                for row in ledger["checks"]
            ])
            ledger_path.write_text(json.dumps(flutter_only))
            self.assertEqual(MODULE.validate_visual_ledger(root), [])
            for gate in ("page_transitions", "background_motion"):
                with self.subTest(missing_second_flutter_page=gate):
                    incomplete = dict(flutter_only, checks=[
                        dict(row, targets=["home"], exclusions={"welcome": "Has native cover"})
                        if row["id"] == gate else row for row in flutter_only["checks"]
                    ])
                    ledger_path.write_text(json.dumps(incomplete))
                    self.assertIn(f"{gate}: Flutter surface has no motion acceptance result: welcome",
                                  MODULE.validate_visual_ledger(root))

    def test_visual_ledger_rejects_uncovered_pages_and_missing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lib/page_module").mkdir(parents=True)
            (root / "lib/page_module/settings_page.dart").write_text("class SettingsPage {}", encoding="utf-8")
            (root / ".codex-work").mkdir()
            (root / ".codex-work/ui-visual-gates.json").write_text(json.dumps({
                "build": {"id": "1", "device": "iPhone 17 Pro Max", "os": "iOS 26.5"},
                "surfaces": [],
                "checks": [{"id": "media", "status": "Verified", "targets": ["settings"],
                            "implementation": ["lib/page_module/settings_page.dart"],
                            "evidence": [".codex-work/missing.png"], "result": "Checked."}]
            }), encoding="utf-8")
            findings = MODULE.validate_visual_ledger(root)
            self.assertTrue(any("settings_page.dart" in item for item in findings))
            self.assertTrue(any("missing.png" in item for item in findings))

    def test_visual_ledger_rejects_duplicate_background_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for page_id in ("home", "task"):
                page = root / f"lib/page_module/{page_id}_page.dart"
                page.parent.mkdir(parents=True, exist_ok=True)
                background = root / f"assets/backgrounds/{page_id}/{page_id}_background.png"
                background.parent.mkdir(parents=True, exist_ok=True)
                background.write_bytes(b"background")
                page.write_text(background.name, encoding="utf-8")
            evidence = root / ".codex-work"
            evidence.mkdir()
            (evidence / "screen.png").write_bytes(b"evidence")
            surfaces = [{"id": page_id, "kind": "flutter", "source": f"lib/page_module/{page_id}_page.dart",
                         "background": {"asset": f"assets/backgrounds/{page_id}/{page_id}_background.png",
                                        "gradient_tokens": ["brandGradient", "sunsetGradient"],
                                        "palette_hex": ["#F05A3C", "#FFB347", "#6F2DBD"]}}
                        for page_id in ("home", "task")]
            checks = [{"id": gate, "status": "Verified", "targets": ["home", "task"],
                       "implementation": ["lib/page_module/home_page.dart"],
                       "evidence": [".codex-work/screen.png"], "result": "Observed."}
                      for gate in ("brand_palette", "gradients", "typography", "particles", "motion",
                                   "backgrounds", "decoration", "icons", "emoji", "text_density", "media", "content", "layout", "controls", "states",
                                   "appearance", "accessibility", "launch_flow", "app_icon", "html", "refinement")]
            ledger = {"build": {"id": "1", "device": "iPhone 17 Pro Max", "os": "iOS 26.5"},
                      "surfaces": surfaces, "checks": checks}
            (evidence / "ui-visual-gates.json").write_text(json.dumps(ledger), encoding="utf-8")
            self.assertIn("task: background bytes duplicate surface home; each surface needs its own decoration",
                          MODULE.validate_visual_ledger(root))

    def test_malformed_ledger_is_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".codex-work").mkdir()
            ledger = root / ".codex-work/ui-visual-gates.json"
            for contents in ("{broken", "[]", '{"build":[],"surfaces":false,"checks":null}'):
                ledger.write_text(contents, encoding="utf-8")
                self.assertTrue(MODULE.validate_visual_ledger(root))


if __name__ == "__main__":
    unittest.main()
