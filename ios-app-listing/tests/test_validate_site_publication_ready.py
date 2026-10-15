import tempfile
import unittest
from pathlib import Path

from validate_site_publication_ready import REQUIRED_PAGES, validate_page_html, validate_site_dir


class ValidateSitePublicationReadyTests(unittest.TestCase):
    def test_accepts_complete_user_facing_copy_without_authoring_markers(self):
        html = """<!doctype html><html><head><title>Privacy Policy</title>
        <meta name="description" content="Privacy information for Aurora Notes"></head>
        <body><main><h1>Privacy Policy</h1><p>Aurora Notes explains how information is handled and describes the choices available when using its features.</p></main></body></html>"""
        self.assertEqual(validate_page_html("PrivacyPolicy.html", html), [])

    def test_rejects_an_empty_shell_even_when_it_has_a_page_title(self):
        html = "<html><head><title>Privacy Policy</title></head><body><main><h1>Privacy Policy</h1></main></body></html>"
        errors = validate_page_html("PrivacyPolicy.html", html)
        self.assertTrue(any("substantive page copy" in error.lower() for error in errors))

    def test_allows_a_confirmed_product_feature_named_drafts(self):
        html = """<html><head><title>Studio Terms</title></head><body><main><h1>Studio Terms</h1>
        <p>Members can save project drafts, return to them later, and continue editing the work they chose to keep.</p>
        <p>These terms describe the available editing features and the responsibilities that apply to their use.</p>
        </main></body></html>"""
        self.assertEqual(validate_page_html("Terms&Conditions.html", html), [])

    def test_rejects_draft_and_placeholder_copy_in_visible_or_accessible_text(self):
        html = """<!doctype html><html><head><title>Draft Privacy Policy</title></head>
        <body><h1>Privacy Policy</h1><p>Pending confirmation.</p>
        <button aria-label="TODO: add contact">Contact</button></body></html>"""
        errors = validate_page_html("PrivacyPolicy.html", html)
        self.assertTrue(any("draft" in error.lower() for error in errors))
        self.assertTrue(any("pending confirmation" in error.lower() for error in errors))
        self.assertTrue(any("todo" in error.lower() for error in errors))

    def test_rejects_a_standalone_draft_watermark_in_the_page_body(self):
        html = """<html><head><title>Privacy Policy</title></head><body>
        <main><h1>Privacy Policy</h1><p>Aurora Notes explains how information is handled with clear detail for readers.</p>
        <span>Draft</span></main></body></html>"""
        errors = validate_page_html("PrivacyPolicy.html", html)
        self.assertTrue(any("draft marker" in error.lower() for error in errors))

    def test_requires_all_four_standalone_pages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_dir = Path(temp_dir)
            for page in REQUIRED_PAGES[:-1]:
                (site_dir / page).write_text("<html><body><main>This completed page contains product information and readable guidance for its visitors.</main></body></html>", encoding="utf-8")
            errors = validate_site_dir(site_dir)
        self.assertTrue(any("Support.html" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
