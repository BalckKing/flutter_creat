#!/usr/bin/env python3
import importlib.util, tempfile, unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_welcome_flow.py"
spec=importlib.util.spec_from_file_location("validate_welcome_flow", SCRIPT); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class WelcomeTests(unittest.TestCase):
    def make(self, source):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); root=Path(temp.name); (root/"lib").mkdir(); (root/"aduit").mkdir(); (root/"lib/welcome.dart").write_text(source, encoding="utf-8"); (root/"aduit/welcome.html").write_text("<html></html>",encoding="utf-8"); return root
    def test_native_welcome_and_clear_data_entry_pass(self):
        root=self.make("""class WelcomePage {}\nvoid flow() { ClearData(); Navigator.of(context).pushNamed('/entry'); Text('Continue'); Text('Enter'); }\n""")
        self.assertEqual(module.validate(root)["status"], "Passed")
    def test_pause_is_rejected(self):
        root=self.make("class WelcomePage {} // Pause\nText('Continue');")
        report=module.validate(root); self.assertEqual(report["status"], "Failed"); self.assertTrue(any("pause" in e.lower() for e in report["errors"]))

if __name__ == "__main__": unittest.main()
