#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "flutter-engine-runner/scripts/run_bounded_command.py"
)


class BoundedCommandTests(unittest.TestCase):
    def run_wrapper(self, command: list[str], *, timeout: float = 3, no_progress: float = 1.0):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "command.log"
            status = root / "command-status.json"
            started = time.monotonic()
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--cwd",
                    str(root),
                    "--timeout-seconds",
                    str(timeout),
                    "--no-progress-seconds",
                    str(no_progress),
                    "--poll-seconds",
                    "0.05",
                    "--output-file",
                    str(output),
                    "--status-file",
                    str(status),
                    "--",
                    *command,
                ],
                text=True,
                capture_output=True,
            )
            elapsed = time.monotonic() - started
            self.assertTrue(status.is_file(), result.stderr)
            return result, json.loads(status.read_text(encoding="utf-8")), elapsed

    def test_successful_build_command_records_passed_status(self):
        result, status, _ = self.run_wrapper(
            [sys.executable, "-c", "print('build complete')"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(status["status"], "passed")
        self.assertEqual(status["exit_code"], 0)
        self.assertIn("build complete", result.stdout)
        self.assertGreaterEqual(status["heartbeat_count"], 1)

    def test_silent_command_is_stopped_after_no_progress(self):
        result, status, elapsed = self.run_wrapper(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout=5,
            no_progress=0.2,
        )
        self.assertEqual(result.returncode, 125, result.stdout + result.stderr)
        self.assertEqual(status["status"], "blocked_no_progress")
        self.assertLess(elapsed, 2.0)
        self.assertIn("no progress", result.stdout.lower())

    def test_timeout_is_distinct_from_no_progress_block(self):
        result, status, elapsed = self.run_wrapper(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout=0.25,
            no_progress=5,
        )
        self.assertEqual(result.returncode, 124, result.stdout + result.stderr)
        self.assertEqual(status["status"], "timeout")
        self.assertLess(elapsed, 2.0)

    def test_output_resets_no_progress_window(self):
        code = "import sys,time; print('phase 1', flush=True); time.sleep(.25); print('phase 2', flush=True)"
        result, status, _ = self.run_wrapper(
            [sys.executable, "-c", code],
            timeout=2,
            no_progress=0.4,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(status["status"], "passed")
        self.assertIn("phase 1", result.stdout)
        self.assertIn("phase 2", result.stdout)


if __name__ == "__main__":
    unittest.main()
