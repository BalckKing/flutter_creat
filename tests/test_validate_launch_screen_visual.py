#!/usr/bin/env python3
import json
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_launch_screen_visual.py"
SPEC = importlib.util.spec_from_file_location("launch_screen_contract", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class NativeLaunchScreenVisualContractTests(unittest.TestCase):
    def make_project(self, *, rich=True, storyboard=True):
        root = Path(tempfile.mkdtemp())
        if storyboard:
            launch = root / "ios/Runner/Base.lproj/LaunchScreen.storyboard"
            launch.parent.mkdir(parents=True)
            launch.write_text(
                "<document scene='LaunchScreen'><view backgroundColor='brandGradient'>"
                "<imageView image='launch_theme_image'/><label text='ProjectName'/><label text='A clear positioning line'/>"
                "<view userLabel='decorative halo'/><view userLabel='brand mark'/></view></document>",
                encoding="utf-8",
            )
        assets = root / "ios/Runner/Assets.xcassets/LaunchTheme.imageset"
        assets.mkdir(parents=True)
        (assets / "launch_theme_image.png").write_bytes(b"theme-image")
        evidence = root / ".work"
        evidence.mkdir()
        (evidence / "launch-screen-current-build.png").write_bytes(b"current-build")
        ledger = self.rich_ledger() if rich else self.minimal_ledger()
        (evidence / "launch-screen-visual.json").write_text(
            json.dumps(ledger, ensure_ascii=False), encoding="utf-8"
        )
        return root

    @staticmethod
    def rich_ledger():
        return {
            "source": "ios/Runner/Base.lproj/LaunchScreen.storyboard",
            "composition": "layered_theme_launch",
            "background": {
                "mode": "gradient",
                "coverage": "full_bleed",
                "tokens": ["launchGradientA", "launchGradientB", "launchGlow"],
            },
            "layers": [
                {"role": "background_gradient", "asset": None},
                {"role": "theme_image", "asset": "ios/Runner/Assets.xcassets/LaunchTheme.imageset/launch_theme_image.png", "opacity": 0.28, "placement": "edge_to_edge_crop"},
                {"role": "brand", "asset": "ios/Runner/Assets.xcassets/LaunchTheme.imageset/launch_theme_image.png", "opacity": 0.96, "placement": "upper_third"},
                {"role": "copy", "text": ["ProjectName", "A clear positioning line"]},
                {"role": "decoration", "asset": None, "placement": "halo_and_framed_accents"},
            ],
            "layout": {
                "type": "layered_composition",
                "single_centered_image": False,
                "empty_area_ratio": 0.34,
            },
            "evidence": [".work/launch-screen-current-build.png"],
        }

    @staticmethod
    def minimal_ledger():
        return {
            "source": "ios/Runner/Base.lproj/LaunchScreen.storyboard",
            "composition": "single_centered_image",
            "background": {"mode": "solid", "coverage": "center_only", "tokens": []},
            "layers": [
                {"role": "background", "color": "#FAF9F2"},
                {"role": "theme_image", "asset": "ios/Runner/Assets.xcassets/LaunchTheme.imageset/launch_theme_image.png", "opacity": 1.0, "placement": "center_small"},
            ],
            "layout": {"type": "single_centered_image", "single_centered_image": True, "empty_area_ratio": 0.82},
            "evidence": [".work/launch-screen-current-build.png"],
        }

    def test_rich_layered_launch_screen_passes(self):
        root = self.make_project(rich=True)
        self.assertEqual(MODULE.validate(root), [])

    def test_rejects_white_single_image_screen(self):
        root = self.make_project(rich=False)
        findings = MODULE.validate(root)
        self.assertTrue(any("single centered image" in item for item in findings))
        self.assertTrue(any("full-bleed" in item for item in findings))
        self.assertTrue(any("layer" in item for item in findings))

    def test_requires_native_storyboard_and_current_build_evidence(self):
        root = self.make_project(rich=True, storyboard=False)
        (root / ".work/launch-screen-current-build.png").unlink()
        findings = MODULE.validate(root)
        self.assertTrue(any("Launch Screen storyboard" in item for item in findings))
        self.assertTrue(any("current-build" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
