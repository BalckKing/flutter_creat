#!/usr/bin/env python3
import importlib.util, json, tempfile, unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_capability_matrix.py"
spec=importlib.util.spec_from_file_location("validate_capability_matrix", SCRIPT); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class CapabilityTests(unittest.TestCase):
    def setUp(self): self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root=Path(self.temp.name); (self.root/".codex-work").mkdir()
    def row(self): return {"capability":"map","real_tool_or_sdk":"MapKit","version":"iOS 27","license/source":"Apple SDK","actual_consumer":"lib/map_page.dart","fallback":"manual location entry","runtime_evidence":[".codex-work/map.mp4"],"formula_record":{"style":"bright","animation":[]},"status":"Runtime verified"}
    def test_real_consumer_passes(self):
        (self.root/".codex-work/capability-matrix.json").write_text(json.dumps({"capabilities":[self.row()]}),encoding="utf-8"); self.assertEqual(module.validate(self.root)["status"],"Passed")
    def test_package_only_consumer_fails(self):
        row=self.row(); row["actual_consumer"]="package"; (self.root/".codex-work/capability-matrix.json").write_text(json.dumps({"capabilities":[row]}),encoding="utf-8"); report=module.validate(self.root); self.assertEqual(report["status"],"Failed"); self.assertTrue(any("package-only" in e for e in report["errors"]))

if __name__ == "__main__": unittest.main()
