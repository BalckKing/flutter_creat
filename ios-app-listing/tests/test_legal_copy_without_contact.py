import tempfile
import unittest
from pathlib import Path

from inspect_common import support_email_facts
from legal_copy import build_faq, build_privacy, build_terms
from render_app_listing import render_privacy_sections, render_support_sections, render_terms_sections
from validate_support_output import validate_support_output


def inspect_payload(support_email=None):
    return {
        "support_email": support_email,
        "support_email_source": "explicit" if support_email else "missing",
        "permissions": {"camera": "Take a photo for a saved entry."},
        "privacy_signals": {},
        "capability_candidates": {},
        "legal_signals": {"matches": {}, "conflicts": []},
        "access_signals": {"mode": "neutral"},
        "messaging_signals": {},
        "beauty_editing_signals": {},
        "ai_signals": {},
        "translation_signals": {},
        "dependencies": [],
        "network_destinations": [],
        "iap_codes": [],
    }


class LegalCopyWithoutContactTests(unittest.TestCase):
    def test_inspection_does_not_invent_a_support_email(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "lib").mkdir()
            self.assertEqual(support_email_facts(root), {"support_email": None, "support_email_source": "missing"})
            (root / "lib" / "support.dart").write_text("const support = 'help@example.test';", encoding="utf-8")
            self.assertEqual(support_email_facts(root), {"support_email": "help@example.test", "support_email_source": "explicit"})

    def test_missing_email_is_not_rendered_as_a_contact_or_placeholder(self):
        payload = inspect_payload()
        privacy = " ".join(section["body"] for section in build_privacy("Aurora Notes", payload, set()))
        terms = " ".join(section["body"] for section in build_terms("Aurora Notes", payload, set()))
        faq = " ".join(item["body"] for item in build_faq(payload, set()))

        for text in (privacy, terms, faq):
            self.assertNotIn("None", text)
            self.assertNotIn("support@", text)
            self.assertNotIn("email support", text.lower())

    def test_pages_omit_contact_panels_when_email_is_not_confirmed(self):
        privacy = render_privacy_sections({"privacy_intro": "This policy describes the app's information practices.", "privacy_sections": [], "support_email": None})
        terms = render_terms_sections({"terms_intro": "These terms describe use of the app.", "terms_sections": [], "support_email": None})
        support = render_support_sections({"faq_items": [{"title": "How does this work?", "body": "Follow the steps shown in the app."}], "support_outro": "Review the answers below.", "support_email": None})

        for html in (privacy, terms, support):
            self.assertNotIn("mailto:", html)
            self.assertNotIn(">None<", html)
        self.assertNotIn("contact-panel", privacy)
        self.assertNotIn("contact-panel", terms)
        self.assertNotIn("contact-panel", support)

    def test_explicit_email_remains_in_the_generated_copy(self):
        payload = inspect_payload("help@example.test")
        privacy = " ".join(section["body"] for section in build_privacy("Aurora Notes", payload, set()))
        self.assertIn("help@example.test", privacy)

    def test_support_validation_does_not_expect_an_unconfirmed_email(self):
        errors = validate_support_output(
            inspect_payload(),
            "Frequently Asked Questions. How does this work? Follow the steps shown in the app. Why is access requested? It supports the selected feature.",
        )
        self.assertFalse(any("email" in error.lower() for error in errors))


if __name__ == "__main__":
    unittest.main()
