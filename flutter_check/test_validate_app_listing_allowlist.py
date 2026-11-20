#!/usr/bin/env python3
import importlib.util, struct, tempfile, unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_app_listing_allowlist.py"
spec=importlib.util.spec_from_file_location("validate_app_listing_allowlist", SCRIPT); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
PNG=b"\x89PNG\r\n\x1a\n" + b"\0"*8 + struct.pack(">II",1206,2622) + b"\0"*8
class AppListingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root=Path(self.temp.name)
        (self.root/"AppListing/site/img").mkdir(parents=True); (self.root/"AppListing/imgs").mkdir()
        for name in ("intro.md","welcome.html"): (self.root/"AppListing"/name).write_text("ok", encoding="utf-8")
        (self.root/"AppListing/site/index.html").write_bytes((self.root/"AppListing/welcome.html").read_bytes())
        for name in ("PrivacyPolicy.html","Terms&Conditions.html","Support.html"): (self.root/"AppListing/site"/name).write_text("ok", encoding="utf-8")
        (self.root/"AppListing/site/img/logo.png").write_bytes(PNG)
        for i in range(2): (self.root/"AppListing/imgs"/f"shot{i}.png").write_bytes(PNG)
    def test_final_allowlist_accepts_variable_evidence_count(self): self.assertEqual(module.validate(self.root, final=True)["status"], "Passed")

    def test_final_allowlist_allows_missing_optional_screenshot_directory(self):
        import shutil
        shutil.rmtree(self.root/"AppListing/imgs")
        self.assertEqual(module.validate(self.root, final=True)["status"], "Passed")
    def test_root_index_and_extra_files_fail(self):
        (self.root/"AppListing/index.html").write_text("bad", encoding="utf-8"); (self.root/"AppListing/extra.txt").write_text("bad", encoding="utf-8")
        report=module.validate(self.root, final=True); self.assertEqual(report["status"], "Failed"); self.assertTrue(any("index.html" in e for e in report["errors"]))

    def test_site_index_must_match_welcome(self):
        (self.root/"AppListing/site/index.html").write_text("different", encoding="utf-8")
        report=module.validate(self.root, final=True)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("byte-identical" in e for e in report["errors"]))

    def test_site_index_is_required(self):
        (self.root/"AppListing/site/index.html").unlink()
        report=module.validate(self.root, final=True)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("site/index.html" in e for e in report["errors"]))

if __name__ == "__main__": unittest.main()
