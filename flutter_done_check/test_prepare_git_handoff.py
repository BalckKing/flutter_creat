#!/usr/bin/env python3
"""Regression tests for the final Git handoff in a real Flutter project root."""
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "flutter-engine-runner/scripts/prepare_git_handoff.py"


def git(root, *args, check=True, env=None):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        env=env,
    )
    if check and result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result


class GitHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "Aurora App"
        (self.root / "lib").mkdir(parents=True)
        (self.root / "ios").mkdir()
        (self.root / "pubspec.yaml").write_text("name: aurora_app\n")
        self.url = "git@example.invalid:team/aurora.git"

    def run_tool(self, *extra, expected=0, env=None):
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(self.root),
             "--repository-url", self.url, *extra],
            text=True,
            capture_output=True,
            env=env,
        )
        self.assertEqual(process.returncode, expected, process.stdout + process.stderr)
        try:
            return json.loads(process.stdout)
        except json.JSONDecodeError as error:
            self.fail(f"tool did not return JSON: {process.stdout!r} {process.stderr!r}: {error}")

    def test_initializes_project_creates_branch_remote_and_stays_uncommitted(self):
        result = self.run_tool()
        self.assertTrue((self.root / ".git").exists())
        self.assertEqual(git(self.root, "symbolic-ref", "--short", "HEAD").stdout.strip(), "feat/1.0.0")
        self.assertEqual(git(self.root, "remote", "get-url", "origin").stdout.strip(), self.url)
        self.assertEqual(git(self.root, "rev-parse", "--verify", "HEAD", check=False).returncode, 128)
        self.assertEqual(result["branch"], "feat/1.0.0")
        self.assertEqual(result["head"]["state"], "unborn")
        self.assertTrue(result["initialized"])
        self.assertTrue(result["ready_to_commit"])
        report = (self.root / ".work/git-handoff.md").read_text()
        self.assertIn("git add", report)
        self.assertIn("未执行", report)
        self.assertIn("已初始化、已关联、等待用户自行提交", report)

    def test_preserves_existing_staged_and_unstaged_changes(self):
        git(self.root, "init", "--initial-branch=main")
        git(self.root, "config", "user.name", "Fixture User")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        (self.root / "lib/main.dart").write_text("first\n")
        git(self.root, "add", "lib/main.dart")
        (self.root / "lib/main.dart").write_text("second\n")
        result = self.run_tool()
        self.assertEqual(result["branch"], "feat/1.0.0")
        self.assertEqual(git(self.root, "symbolic-ref", "--short", "HEAD").stdout.strip(), "feat/1.0.0")
        status = git(self.root, "status", "--porcelain=v1").stdout
        self.assertIn("AM lib/main.dart", status)
        self.assertIn("AM lib/main.dart", result["workspace"]["status_before_report"])

    def test_conflicting_existing_target_branch_is_rejected_without_rewriting_remote(self):
        git(self.root, "init", "--initial-branch=main")
        git(self.root, "config", "user.name", "Fixture User")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        (self.root / "lib/main.dart").write_text("main\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "main")
        main_head = git(self.root, "rev-parse", "HEAD").stdout.strip()
        git(self.root, "switch", "-c", "feat/1.0.0")
        (self.root / "lib/other.dart").write_text("branch\n")
        git(self.root, "add", "lib/other.dart")
        git(self.root, "commit", "-m", "feature")
        feature_head = git(self.root, "rev-parse", "HEAD").stdout.strip()
        git(self.root, "switch", "main")
        result = self.run_tool(expected=1)
        self.assertFalse(result["ready_to_commit"])
        self.assertEqual(git(self.root, "symbolic-ref", "--short", "HEAD").stdout.strip(), "main")
        self.assertEqual(git(self.root, "rev-parse", "refs/heads/feat/1.0.0").stdout.strip(), feature_head)
        self.assertEqual(git(self.root, "rev-parse", "HEAD").stdout.strip(), main_head)
        self.assertFalse((self.root / ".git/config").read_text().find(self.url) >= 0)

    def test_parent_repository_is_never_reused_for_project(self):
        parent = Path(self.temp.name) / "parent"
        parent.mkdir()
        git(parent, "init", "--initial-branch=main")
        child = parent / "child"
        (child / "lib").mkdir(parents=True)
        (child / "ios").mkdir()
        (child / "pubspec.yaml").write_text("name: child\n")
        self.root = child
        result = self.run_tool(expected=1)
        self.assertFalse(result["initialized"])
        self.assertFalse((child / ".git").exists())

    def test_existing_different_origin_is_preserved_and_user_remote_is_added(self):
        git(self.root, "init", "--initial-branch=feat/1.0.0")
        git(self.root, "config", "user.name", "Fixture User")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        git(self.root, "remote", "add", "origin", "git@example.invalid:old/aurora.git")
        result = self.run_tool()
        self.assertEqual(git(self.root, "remote", "get-url", "origin").stdout.strip(), "git@example.invalid:old/aurora.git")
        self.assertEqual(git(self.root, "remote", "get-url", result["remote"]["name"]).stdout.strip(), self.url)
        self.assertNotEqual(result["remote"]["name"], "origin")

    def test_missing_identity_is_reported_without_inventing_one(self):
        git(self.root, "init", "--initial-branch=feat/1.0.0")
        env = os.environ.copy()
        env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(Path(self.temp.name) / "empty-global")})
        result = self.run_tool(expected=1, env=env)
        self.assertFalse(result["identity"]["can_commit"])
        self.assertIn("user.name", result["identity"]["missing"])
        self.assertIn("user.email", result["identity"]["missing"])
        self.assertEqual(git(self.root, "config", "--local", "--get", "user.name", check=False).returncode, 1)
        self.assertEqual(git(self.root, "config", "--local", "--get", "user.email", check=False).returncode, 1)

    def test_in_progress_merge_is_rejected_before_branch_or_remote_changes(self):
        git(self.root, "init", "--initial-branch=main")
        git(self.root, "config", "user.name", "Fixture User")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        (self.root / "lib/main.dart").write_text("main\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "main")
        merge_head = git(self.root, "rev-parse", "HEAD").stdout.strip()
        (self.root / ".git/MERGE_HEAD").write_text(merge_head + "\n")
        result = self.run_tool(expected=1)
        self.assertFalse(result["ready_to_commit"])
        self.assertEqual(git(self.root, "symbolic-ref", "--short", "HEAD").stdout.strip(), "main")
        self.assertEqual(git(self.root, "remote", check=False).stdout.strip(), "")
        self.assertIn("merge", " ".join(result["errors"]).lower())

    def test_in_progress_operation_is_rejected_even_when_already_on_target_branch(self):
        git(self.root, "init", "--initial-branch=feat/1.0.0")
        (self.root / ".git/MERGE_HEAD").write_text("deadbeef\n")
        result = self.run_tool(expected=1)
        self.assertFalse(result["ready_to_commit"])
        self.assertEqual(git(self.root, "remote", check=False).stdout.strip(), "")
        self.assertIn("merge", " ".join(result["errors"]).lower())


if __name__ == "__main__":
    unittest.main()
