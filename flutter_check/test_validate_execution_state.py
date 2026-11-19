#!/usr/bin/env python3
import importlib.util, json, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/validate_execution_state.py"
spec=importlib.util.spec_from_file_location("validate_execution_state", SCRIPT); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class ExecutionStateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root=Path(self.temp.name); (self.root/".codex-work").mkdir(); self.now=datetime(2026,11,18,12,tzinfo=timezone.utc)
    def state(self):
        stamp=self.now.isoformat(); return {"schema_version":1,"run_id":"r1","status":"running","started_at":stamp,"heartbeat_at":stamp,"retry_count":0,"tasks":[{"id":"ios","status":"running","started_at":stamp,"heartbeat_at":stamp,"retry_count":0,"resume_action":"rerun source check"}]}
    def test_valid_state(self):
        (self.root/".codex-work/execution-state.json").write_text(json.dumps(self.state()),encoding="utf-8"); self.assertEqual(module.validate(self.root,now=self.now)["status"],"Passed")
    def test_stale_heartbeat_fails(self):
        data=self.state(); data["heartbeat_at"]="2026-11-18T11:00:00+00:00"; data["tasks"][0]["heartbeat_at"]=data["heartbeat_at"]; (self.root/".codex-work/execution-state.json").write_text(json.dumps(data),encoding="utf-8"); report=module.validate(self.root,now=self.now); self.assertEqual(report["status"],"Failed"); self.assertTrue(any("stale" in e for e in report["errors"]))

if __name__ == "__main__": unittest.main()
