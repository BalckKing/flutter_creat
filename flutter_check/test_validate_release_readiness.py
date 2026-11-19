#!/usr/bin/env python3
import importlib.util, json, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_release_readiness.py"
spec=importlib.util.spec_from_file_location("validate_release_readiness", SCRIPT); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class ReadinessTests(unittest.TestCase):
    def setUp(self): self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root=Path(self.temp.name); (self.root/".codex-work").mkdir()
    def gates(self,status="Passed"):
        return [{"name":n,"status":status,"evidence":[f".codex-work/{n}.json"]} for n in ("runtime","ios_artifacts","aduit","quality_records","asset_staging","generation_cleanup","logo_quality","final_visual_product","git_handoff")]
    def generated_at(self):
        return (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    def test_ready_requires_all_passed(self):
        data={"generated_at":self.generated_at(),"release_readiness":"Ready for submission","gates":self.gates()}; (self.root/".codex-work/release-readiness.json").write_text(json.dumps(data),encoding="utf-8"); self.assertEqual(module.validate(self.root)["status"],"Passed")
    def test_missing_runtime_evidence_cannot_be_ready(self):
        data={"generated_at":self.generated_at(),"release_readiness":"Ready for submission","gates":self.gates()}; data["gates"][0]["status"]="Not verified"; (self.root/".codex-work/release-readiness.json").write_text(json.dumps(data),encoding="utf-8"); report=module.validate(self.root); self.assertEqual(report["status"],"Failed"); self.assertEqual(report["release_readiness"],"Not ready")

    def test_missing_asset_staging_gate_cannot_be_ready(self):
        data={"generated_at":self.generated_at(),"release_readiness":"Ready for submission","gates":self.gates()}
        data["gates"]=[gate for gate in data["gates"] if gate["name"] != "asset_staging"]
        (self.root/".codex-work/release-readiness.json").write_text(json.dumps(data),encoding="utf-8")
        report=module.validate(self.root)
        self.assertEqual(report["status"],"Failed")
        self.assertTrue(any("asset_staging" in error for error in report["errors"]))

    def test_missing_final_visual_product_gate_cannot_be_ready(self):
        data={"generated_at":self.generated_at(),"release_readiness":"Ready for submission","gates":self.gates()}
        data["gates"]=[gate for gate in data["gates"] if gate["name"] != "final_visual_product"]
        (self.root/".codex-work/release-readiness.json").write_text(json.dumps(data),encoding="utf-8")
        report=module.validate(self.root)
        self.assertEqual(report["status"],"Failed")
        self.assertTrue(any("final_visual_product" in error for error in report["errors"]))

    def test_unverified_final_visual_product_forces_not_ready(self):
        data={"generated_at":self.generated_at(),"release_readiness":"Ready for submission","gates":self.gates()}
        next(gate for gate in data["gates"] if gate["name"] == "final_visual_product")["status"] = "Not verified"
        (self.root/".codex-work/release-readiness.json").write_text(json.dumps(data),encoding="utf-8")
        report=module.validate(self.root)
        self.assertEqual(report["status"],"Failed")
        self.assertEqual(report["release_readiness"],"Not ready")

    def test_generated_at_and_evidence_paths_are_required(self):
        data={"release_readiness":"Not ready","gates":self.gates()}
        data["gates"][0]["evidence"]=[""]
        (self.root/".codex-work/release-readiness.json").write_text(json.dumps(data),encoding="utf-8")
        report=module.validate(self.root)
        self.assertEqual(report["status"],"Failed")
        self.assertTrue(any("generated_at" in error for error in report["errors"]))
        self.assertTrue(any("evidence" in error for error in report["errors"]))

if __name__ == "__main__": unittest.main()
