#!/usr/bin/env python3
import hashlib, importlib.util, json, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_work_records.py"
spec = importlib.util.spec_from_file_location("validate_work_records", SCRIPT)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class WorkRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.records = self.root / ".codex-work/records"; self.records.mkdir(parents=True)
        self.now = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
        evidence = self.root / ".codex-work/evidence.png"; evidence.write_bytes(b"evidence")
        digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
        self.record = {
            "schema_version": 1, "run_id": "run-1", "project_root": str(self.root),
            "bundle_id": "com.example.app", "build_id": "build-1", "device": "iPhone Simulator",
            "udid": "SIM-1", "recorded_at": self.now.isoformat(), "freshness_window_hours": 24,
            "status": "Passed", "next_action": "None",
            "evidence": [{"path": ".codex-work/evidence.png", "sha256": digest,
                          "captured_at": (self.now - timedelta(minutes=1)).isoformat(),
                          "source": "same build", "kind": "screenshot", "build_id": "build-1",
                          "device": "iPhone Simulator", "udid": "SIM-1"}],
        }
    def test_valid_record(self):
        (self.records / "ui.json").write_text(json.dumps(self.record), encoding="utf-8")
        report = module.validate(self.root, now=self.now)
        self.assertEqual(report["status"], "Passed", report)
    def test_stale_evidence_fails(self):
        self.record["evidence"][0]["captured_at"] = (self.now - timedelta(days=3)).isoformat()
        (self.records / "ui.json").write_text(json.dumps(self.record), encoding="utf-8")
        report = module.validate(self.root, now=self.now)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("older than freshness" in e for e in report["errors"]))
    def test_missing_records_are_not_passed(self):
        self.records.rmdir()
        report = module.validate(self.root, now=self.now)
        self.assertEqual(report["status"], "Not verified")
    def test_build_identity_mismatch_fails(self):
        self.record["evidence"][0]["build_id"] = "other"
        (self.records / "ui.json").write_text(json.dumps(self.record), encoding="utf-8")
        report = module.validate(self.root, now=self.now)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("build_id must match" in e for e in report["errors"]))

if __name__ == "__main__": unittest.main()
