#!/usr/bin/env python3
"""Initialize a Flutter project for a user-controlled Git handoff.

The command deliberately stops before staging, committing, or pushing.  It only
creates the project's own repository when needed, prepares ``feat/1.0.0``,
records the requested remote, and writes a reviewable handoff report.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Tuple


TARGET_BRANCH = "feat/1.0.0"
REPORT_PATH = Path(".work/git-handoff.md")


class HandoffError(RuntimeError):
    """A safe, actionable handoff failure."""


class GitRunner:
    def __init__(self, root: Path, actions: List[Dict[str, Any]]) -> None:
        self.root = root
        self.actions = actions

    def run(self, args: Sequence[str], *, check: bool = False) -> subprocess.CompletedProcess:
        command = ["git", "-C", str(self.root), *args]
        try:
            result = subprocess.run(command, text=True, capture_output=True)
        except OSError as error:
            self.actions.append({"command": command, "returncode": None, "error": str(error)})
            raise HandoffError(f"无法运行 Git：{error}") from error
        self.actions.append(
            {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        )
        if check and result.returncode:
            detail = result.stderr.strip() or result.stdout.strip() or "未知 Git 错误"
            raise HandoffError(f"Git 命令失败（{result.returncode}）：{' '.join(command)}：{detail}")
        return result


def fail_result(message: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    return {
        "scope": "git-handoff",
        "project_root": str(root) if root else None,
        "initialized": False,
        "repository_owned_by_project": False,
        "branch": None,
        "branch_before": None,
        "remote": {"name": None, "url": None, "source": None, "fetch_urls": [], "push_urls": [], "action": None},
        "head": {"state": "unknown", "value": None},
        "head_before": {"state": "unknown", "value": None},
        "identity": {"name": None, "email": None, "missing": [], "can_commit": False},
        "workspace": {"status_before_report": "", "status_after_report": ""},
        "ready_to_commit": False,
        "report": None,
        "actions": [],
        "errors": [message],
        "safety": {
            "git_add": "not executed",
            "git_commit": "not executed",
            "git_push": "not executed",
        },
    }


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def require_flutter_root(root: Path) -> None:
    if not root.exists() or not root.is_dir():
        raise HandoffError(f"工程根目录不存在或不是目录：{root}")
    if root.is_symlink():
        raise HandoffError(f"拒绝通过符号链接操作工程根目录：{root}")
    required = ("pubspec.yaml", "lib", "ios")
    missing = [name for name in required if not (root / name).exists()]
    if missing:
        raise HandoffError(
            "目标目录不是可识别的 Flutter 工程根目录；缺少：" + ", ".join(missing)
        )


def reject_parent_repository(root: Path, runner: GitRunner) -> None:
    dot_git = root / ".git"
    if dot_git.is_symlink():
        raise HandoffError(f"拒绝使用符号链接 .git：{dot_git}")
    if dot_git.exists():
        return
    probe = runner.run(["rev-parse", "--show-toplevel"])
    if probe.returncode == 0 and probe.stdout.strip():
        parent_root = Path(probe.stdout.strip()).resolve()
        if parent_root != root.resolve():
            raise HandoffError(
                f"目标工程被父仓库控制：{parent_root}；为避免误操作资料包/父仓库，请先为工程准备独立目录。"
            )


def verify_own_repository(root: Path, runner: GitRunner) -> None:
    inside = runner.run(["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        raise HandoffError("目标目录尚未成为独立 Git 工作树。")
    top = runner.run(["rev-parse", "--show-toplevel"], check=True).stdout.strip()
    if Path(top).resolve() != root.resolve():
        raise HandoffError(f"Git 根目录不是目标工程本身：{top}")
    git_dir = runner.run(["rev-parse", "--git-dir"], check=True).stdout.strip()
    # A linked worktree has a .git file whose actual git dir lives in another
    # repository.  It cannot satisfy the requirement for an independent app
    # repository, so stop before changing branches or remotes.
    dot_git = root / ".git"
    if dot_git.is_file():
        resolved_git_dir = Path(git_dir)
        if not resolved_git_dir.is_absolute():
            resolved_git_dir = (root / resolved_git_dir).resolve()
        if not is_within(resolved_git_dir, root.resolve()):
            raise HandoffError("目标目录是共享 Git worktree，不是拥有自己 .git 的工程仓库。")


def reject_in_progress_operation(root: Path, runner: GitRunner) -> None:
    markers = {
        "MERGE_HEAD": "merge",
        "CHERRY_PICK_HEAD": "cherry-pick",
        "REVERT_HEAD": "revert",
        "BISECT_START": "bisect",
    }
    git_dir_value = runner.run(["rev-parse", "--git-dir"], check=True).stdout.strip()
    git_dir = Path(git_dir_value)
    if not git_dir.is_absolute():
        git_dir = (root / git_dir).resolve()
    active = [label for marker, label in markers.items() if (git_dir / marker).exists()]
    if active:
        raise HandoffError(
            "仓库处于未完成的 " + ", ".join(active) + " 操作中；为保护分支和索引，未执行 Git 交接。"
        )


def initialize_repository(root: Path, runner: GitRunner) -> bool:
    if (root / ".git").exists():
        verify_own_repository(root, runner)
        return False
    first = runner.run(["init", f"--initial-branch={TARGET_BRANCH}"])
    if first.returncode and (root / ".git").exists():
        raise HandoffError(
            "Git 初始化返回失败且留下了 .git；为避免继续修改不完整仓库，已停止，请人工检查。"
        )
    if not (root / ".git").exists():
        # Git versions before 2.28 do not know --initial-branch.  Retry only
        # when the first invocation did not create a repository.
        runner.run(["init"], check=True)
        runner.run(["symbolic-ref", "HEAD", f"refs/heads/{TARGET_BRANCH}"], check=True)
    elif first.returncode:
        raise HandoffError(f"Git 初始化失败：{first.stderr.strip() or first.stdout.strip()}")
    verify_own_repository(root, runner)
    return True


def head_state(runner: GitRunner) -> Tuple[bool, Optional[str]]:
    result = runner.run(["rev-parse", "--verify", "HEAD"])
    if result.returncode:
        return False, None
    return True, result.stdout.strip()


def current_branch(runner: GitRunner) -> Optional[str]:
    result = runner.run(["symbolic-ref", "--quiet", "--short", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def branch_tip(runner: GitRunner, name: str) -> Optional[str]:
    result = runner.run(["rev-parse", "--verify", f"refs/heads/{name}"])
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def prepare_branch(runner: GitRunner) -> str:
    has_head, head = head_state(runner)
    branch = current_branch(runner)
    target_tip = branch_tip(runner, TARGET_BRANCH)

    if target_tip is not None and (not has_head or target_tip != head) and branch != TARGET_BRANCH:
        raise HandoffError(
            f"目标分支 {TARGET_BRANCH} 已存在且指向其他提交；为保护现有历史，未切换或覆盖它。"
        )

    if branch == TARGET_BRANCH:
        return TARGET_BRANCH

    if target_tip is not None:
        if has_head and target_tip == head:
            runner.run(["switch", TARGET_BRANCH], check=True)
            return TARGET_BRANCH
        raise HandoffError(f"无法安全复用已有分支：{TARGET_BRANCH}")

    if has_head:
        runner.run(["switch", "-c", TARGET_BRANCH], check=True)
    else:
        # An unborn repository can be renamed without creating an empty commit.
        runner.run(["symbolic-ref", "HEAD", f"refs/heads/{TARGET_BRANCH}"], check=True)
    return TARGET_BRANCH


def remote_urls(runner: GitRunner, name: str) -> List[str]:
    result = runner.run(["config", "--get-all", f"remote.{name}.url"])
    if result.returncode:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def remote_push_urls(runner: GitRunner, name: str) -> List[str]:
    result = runner.run(["config", "--get-all", f"remote.{name}.pushurl"])
    if result.returncode:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def remote_names(runner: GitRunner) -> List[str]:
    result = runner.run(["remote"])
    if result.returncode:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def prepare_remote(runner: GitRunner, requested: str) -> Tuple[str, str]:
    requested = requested.strip()
    if not requested:
        raise HandoffError("Git 仓库地址不能为空。")
    names = remote_names(runner)
    for name in names:
        fetch = remote_urls(runner, name)
        push = remote_push_urls(runner, name)
        if fetch and all(url == requested for url in fetch) and (not push or all(url == requested for url in push)):
            return name, "reused-existing-url"

    if "origin" not in names:
        runner.run(["remote", "add", "origin", requested], check=True)
        return "origin", "added-origin"

    candidate = "user-origin"
    index = 2
    while candidate in names:
        candidate = f"user-origin-{index}"
        index += 1
    runner.run(["remote", "add", candidate, requested], check=True)
    return candidate, "added-preserving-origin"


def read_identity(runner: GitRunner) -> Dict[str, Any]:
    values: Dict[str, Optional[str]] = {}
    missing: List[str] = []
    for key in ("user.name", "user.email"):
        result = runner.run(["config", "--get", key])
        value = result.stdout.strip() if result.returncode == 0 else ""
        values[key] = value or None
        if not value:
            missing.append(key)

    can_commit = not missing
    if can_commit:
        identity = runner.run(["var", "GIT_AUTHOR_IDENT"])
        can_commit = identity.returncode == 0
        if not can_commit:
            missing.append("valid Git author identity")
    return {
        "name": values["user.name"],
        "email": values["user.email"],
        "missing": missing,
        "can_commit": can_commit,
    }


def status_text(runner: GitRunner) -> str:
    result = runner.run(["status", "--porcelain=v1", "--untracked-files=all"])
    if result.returncode:
        return f"<status unavailable: {result.stderr.strip()}>"
    return result.stdout


def safe_report_path(root: Path) -> Path:
    work = root / REPORT_PATH.parent
    if work.exists() and work.is_symlink():
        raise HandoffError(f"拒绝写入符号链接目录：{work}")
    if work.exists() and not work.is_dir():
        raise HandoffError(f"Git 交接记录目录不是目录：{work}")
    work.mkdir(parents=True, exist_ok=True)
    report = root / REPORT_PATH
    if report.exists() and report.is_symlink():
        raise HandoffError(f"拒绝覆盖符号链接：{report}")
    return report


def write_report(root: Path, result: Dict[str, Any]) -> Path:
    report = safe_report_path(root)
    remote = result["remote"]
    head = result["head"]
    identity = result["identity"]
    workspace = result["workspace"]
    lines = [
        "# Git handoff",
        "",
        "本记录由最终验收后的 Git 交接工具生成。它只准备工程仓库，等待用户自行暂存和提交。",
        "",
        f"- 工程根目录：`{result['project_root']}`",
        f"- 仓库是否在本次初始化：`{'yes' if result['initialized'] else 'no'}`",
        f"- 工程拥有独立 `.git`：`{'yes' if result['repository_owned_by_project'] else 'no'}`",
        f"- 交接前分支：`{result.get('branch_before') or 'detached/unborn'}`",
        f"- 当前分支：`{result['branch'] or 'unknown'}`",
        f"- 交接前 HEAD：`{result['head_before']['state']}`" + (f" (`{result['head_before']['value']}`)" if result['head_before'].get("value") else ""),
        f"- HEAD：`{head['state']}`" + (f" (`{head['value']}`)" if head.get("value") else ""),
        f"- 用户仓库地址：`{remote.get('url') or 'unknown'}`",
        f"- 地址来源：`{remote.get('source') or 'unknown'}`",
        f"- remote：`{remote.get('name') or 'unknown'}`（{remote.get('action') or 'not configured'}）",
        f"- fetch URL：`{'`; `'.join(remote.get('fetch_urls') or []) or 'none'}`",
        f"- push URL：`{'`; `'.join(remote.get('push_urls') or []) or 'uses fetch URL'}`",
        f"- Git 用户名：`{identity.get('name') or 'missing'}`",
        f"- Git 邮箱：`{identity.get('email') or 'missing'}`",
        f"- 可直接提交：`{'yes' if identity.get('can_commit') else 'no'}`",
        f"- 交接结果：`{('已初始化、已关联、等待用户自行提交' if result.get('ready_to_commit') else '未完成；请先处理上面的阻断项')}`",
        "",
        "## 工作区",
        "",
        "交接前状态（保留既有暂存与未暂存改动）：",
        "```text",
        workspace.get("status_before_report", ""),
        "```",
        "",
        "交接记录写入后的状态（报告本身可由用户决定是否暂存）：",
        "```text",
        workspace.get("status_after_report", ""),
        "```",
        "",
        "## 安全边界",
        "",
        "- `git add`：未执行",
        "- `git commit`：未执行",
        "- `git push`：未执行",
        "- 没有创建初始空提交；unborn 仓库保持无首个提交。",
        "- 已有 remote 与分支冲突时保留原配置并记录错误，不覆盖历史。",
        "",
        "## 命令记录",
        "",
        "```json",
        json.dumps(result.get("actions", []), ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    content = "\n".join(lines)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=report.parent, prefix=".git-handoff-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        os.replace(temporary, report)
    finally:
        if temporary.exists():
            temporary.unlink()
    return report


def execute(root: Path, requested_url: str, repository_source: str) -> Tuple[Dict[str, Any], int]:
    result = fail_result("", root=root)
    result["errors"] = []
    actions: List[Dict[str, Any]] = []
    result["actions"] = actions
    try:
        require_flutter_root(root)
        runner = GitRunner(root, actions)
        reject_parent_repository(root, runner)
        created = initialize_repository(root, runner)
        result["initialized"] = created
        result["repository_owned_by_project"] = True
        reject_in_progress_operation(root, runner)
        before_has_head, before_head = head_state(runner)
        result["branch_before"] = current_branch(runner)
        result["head_before"] = {"state": "committed" if before_has_head else "unborn", "value": before_head}
        branch = prepare_branch(runner)
        result["branch"] = branch
        remote_name, remote_action = prepare_remote(runner, requested_url)
        result["remote"] = {
            "name": remote_name,
            "url": requested_url.strip(),
            "source": repository_source.strip() or "user-provided command argument",
            "fetch_urls": remote_urls(runner, remote_name),
            "push_urls": remote_push_urls(runner, remote_name),
            "action": remote_action,
        }
        identity = read_identity(runner)
        result["identity"] = identity
        before = status_text(runner)
        result["workspace"]["status_before_report"] = before
        has_head, head = head_state(runner)
        result["head"] = {"state": "committed" if has_head else "unborn", "value": head}
        result["ready_to_commit"] = bool(
            result["repository_owned_by_project"]
            and branch == TARGET_BRANCH
            and remote_name
            and identity["can_commit"]
        )
        if not identity["can_commit"]:
            result["errors"].append(
                "无法直接提交：请在工程仓库配置 user.name 和 user.email；工具不会擅自编造身份。"
            )
        report = write_report(root, result)
        result["report"] = str(report)
        result["workspace"]["status_after_report"] = status_text(runner)
        # Rewrite once so the persisted record includes the post-report state;
        # the report itself is already part of that state on this second pass.
        write_report(root, result)
        return result, 0 if result["ready_to_commit"] else 1
    except HandoffError as error:
        result["errors"].append(str(error))
        # Parent-repository refusal must not write into the parent worktree.
        if result.get("repository_owned_by_project"):
            try:
                report = write_report(root, result)
                result["report"] = str(report)
                if actions:
                    result["workspace"]["status_after_report"] = status_text(GitRunner(root, actions))
                    write_report(root, result)
            except HandoffError as report_error:
                result["errors"].append(f"无法写入交接记录：{report_error}")
        return result, 1
    except (OSError, ValueError) as error:
        result["errors"].append(str(error))
        return result, 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument(
        "--repository-source",
        default="user-provided command argument",
        help="Optional provenance note for the user-supplied repository URL.",
    )
    args = parser.parse_args(argv)
    root = args.project_root.expanduser().resolve()
    result, status = execute(root, args.repository_url, args.repository_source)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return status


if __name__ == "__main__":
    sys.exit(main())
