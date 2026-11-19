#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/cleanup_generation_history.py"
spec = importlib.util.spec_from_file_location("cleanup_generation_history", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CleanupHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".codex-work").mkdir()

    def record(self):
        deleted_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
        return {
            "schema_version": 1,
            "provider_url": "http://stargate.local:3100/",
            "cleanup_required": True,
            "trigger": "after_download",
            "download_status": "completed",
            "status": "completed",
            "task_ids": ["task-01", "task-02"],
            "downloaded_asset_paths": [
                "/Users/admin/Downloads/Bright_Harbor/logo-candidates/c01/result.png",
                "/Users/admin/Downloads/Bright_Harbor/logo-candidates/c02/result.png",
            ],
            "deleted_task_ids": ["task-01", "task-02"],
            "deleted_at": deleted_at,
            "executor": "provider-ui",
            "evidence": [".codex-work/evidence/stargate-history-after.png"],
        }

    def write(self, data):
        (self.root / ".codex-work/generation-cleanup.json").write_text(json.dumps(data), encoding="utf-8")

    def test_exact_post_download_deletion_record_passes(self):
        self.write(self.record())
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Passed", report)

    def test_pending_cleanup_is_blocked(self):
        data = self.record()
        data["status"] = "pending"
        data["deleted_task_ids"] = []
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("status" in error for error in report["errors"]))

    def test_deletion_before_download_is_rejected(self):
        data = self.record()
        data["download_status"] = "in_progress"
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("download_status" in error for error in report["errors"]))

    def test_foreign_or_partial_task_deletion_is_rejected(self):
        data = self.record()
        data["deleted_task_ids"] = ["task-01", "foreign-task"]
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("exactly match" in error for error in report["errors"]))

    def test_unknown_provider_action_is_rejected(self):
        data = self.record()
        data["executor"] = "guessed-api"
        self.write(data)
        report = module.validate(self.root)
        self.assertEqual(report["status"], "Failed")
        self.assertTrue(any("executor" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
