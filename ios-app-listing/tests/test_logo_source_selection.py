import tempfile
import unittest
from pathlib import Path

from generate_app_listing import AboutDeploymentOptions, copy_logo, generate_for_target, pick_logo_source
from inspect_common import find_logo_candidates, is_valid_image_file


# A hand-checked 1x1 RGB PNG. The fixture is deliberately tiny; the selector
# must validate the file signature rather than infer image validity from a
# filename or extension.
VALID_PNG = bytes.fromhex(
    "89504e470d0a1a0a"
    "0000000d4948445200000001000000010802000000907753de"
    "0000000c49444154789c63f8cfc0000003010100c9fe92ef"
    "0000000049454e44ae426082"
)


class LogoSourceSelectionTests(unittest.TestCase):
    def test_truncated_image_is_rejected_even_with_png_signature_and_dimensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "logo.png"
            source.write_bytes(VALID_PNG[:24])
            self.assertFalse(is_valid_image_file(source))

    def test_inspector_does_not_offer_html_or_broken_icon_candidates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            icon_dir = root / "ios/Runner/Assets.xcassets/AppIcon.appiconset"
            icon_dir.mkdir(parents=True)
            (icon_dir / "old.png").write_text("<html>image service</html>", encoding="utf-8")
            (icon_dir / "broken.png").write_bytes(VALID_PNG[:24])
            self.assertEqual(find_logo_candidates(root, "notes"), [])

    def test_missing_logo_does_not_stop_local_listing_pages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pubspec.yaml").write_text("name: field_notes\ndescription: Record nature observations and notes.\n", encoding="utf-8")
            (root / "lib").mkdir()
            (root / "lib/main.dart").write_text("const title = 'Field Notes';\nconst purpose = 'Record nature observations and notes.';\n", encoding="utf-8")
            (root / "assets").mkdir()
            (root / "assets/logo.png").write_text("<!doctype html><html>Stargate UI</html>", encoding="utf-8")

            summary = generate_for_target(
                root, "concise",
                deployment_options=AboutDeploymentOptions(enabled=False, sync_project_listing_urls=False),
                style_state_path=root / "style-state.json",
            )

            self.assertTrue((root / "AppListing/Intro.md").is_file())
            for page in ("index.html", "PrivacyPolicy.html", "Terms&Conditions.html", "Support.html"):
                self.assertGreater((root / "AppListing/site" / page).stat().st_size, 100)
            self.assertFalse((root / "AppListing/site/img/logo.png").exists())
            self.assertIsNone(summary["logo_source"])
            self.assertIn("required_logo_missing", summary["media_review_errors"])
            self.assertFalse(summary["publication_ready"])

    def test_assets_logo_is_preferred_over_stale_app_icon(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            logo = root / "assets" / "logo.png"
            icon = root / "ios/Runner/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png"
            logo.parent.mkdir(parents=True)
            icon.parent.mkdir(parents=True)
            logo.write_bytes(VALID_PNG)
            icon.write_bytes(VALID_PNG)

            selected = pick_logo_source(
                root,
                {"logo_candidates": [str(icon.relative_to(root))]},
            )

            self.assertEqual(selected, logo.resolve())

    def test_html_saved_as_png_is_rejected_and_valid_icon_is_used(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            logo = root / "assets" / "logo.png"
            icon = root / "ios/Runner/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png"
            logo.parent.mkdir(parents=True)
            icon.parent.mkdir(parents=True)
            logo.write_text("<!doctype html><html><body>generator</body></html>", encoding="utf-8")
            icon.write_bytes(VALID_PNG)

            selected = pick_logo_source(
                root,
                {"logo_candidates": [str(logo.relative_to(root)), str(icon.relative_to(root))]},
            )

            self.assertEqual(selected, icon.resolve())

    def test_copied_listing_logo_is_the_image_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "assets/logo.png"
            destination = root / "AppListing/site/img/logo.png"
            source.parent.mkdir(parents=True)
            source.write_bytes(VALID_PNG)

            copy_logo(source, destination)

            self.assertEqual(destination.read_bytes(), VALID_PNG)


if __name__ == "__main__":
    unittest.main()
