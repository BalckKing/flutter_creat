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
            background = root / "assets/backgrounds/home/home_background.png"
            background.parent.mkdir(parents=True)
            background.write_bytes(b"background-fixture")
            (evidence / "ui-visual-gates.json").write_text(json.dumps({
                "build": {"id": "1.0.0+1", "device": "iPhone 17 Pro Max", "os": "iOS 26.5"},
                "surfaces": [{"id": "home", "kind": "flutter", "source": "lib/page_module/home_page.dart",
                              "background": {"asset": "assets/backgrounds/home/home_background.png",
                                             "gradient_tokens": ["brandGradient", "sunsetGradient"],
                                             "palette_hex": ["#F05A3C", "#FFB347", "#6F2DBD"]}}],
                "checks": [{"id": gate, "status": "Verified", "targets": ["home"],
                            "implementation": ["lib/page_module/home_page.dart"],
                            "evidence": [".codex-work/home.png"], "result": "Observed on the recorded build."}
                           for gate in ("brand_palette", "gradients", "typography", "particles", "motion",
                                        "backgrounds", "decoration", "media", "content", "layout", "controls", "states",
                                        "appearance", "accessibility", "launch_flow", "app_icon", "html", "refinement")]
            }), encoding="utf-8")
            self.assertEqual(MODULE.validate_visual_ledger(root), [])

            ledger_path = evidence / "ui-visual-gates.json"
            ledger = json.loads(ledger_path.read_text())
            ledger["checks"] = [row for row in ledger["checks"] if row["id"] != "decoration"]
            ledger_path.write_text(json.dumps(ledger))
            self.assertTrue(any("decoration" in item for item in MODULE.validate_visual_ledger(root)))

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

    def test_visual_ledger_rejects_single_background_signature(self):
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
                                   "backgrounds", "decoration", "media", "content", "layout", "controls", "states",
                                   "appearance", "accessibility", "launch_flow", "app_icon", "html", "refinement")]
            ledger = {"build": {"id": "1", "device": "iPhone 17 Pro Max", "os": "iOS 26.5"},
                      "surfaces": surfaces, "checks": checks}
            (evidence / "ui-visual-gates.json").write_text(json.dumps(ledger), encoding="utf-8")
            self.assertTrue(any("identical background" in item for item in MODULE.validate_visual_ledger(root)))

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
