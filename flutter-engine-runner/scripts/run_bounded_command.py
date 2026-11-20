#!/usr/bin/env python3
"""Run one long build/debug command with bounded progress polling.

This wrapper is intentionally a one-shot replacement for repeatedly polling an
interactive terminal session. It emits command output as it arrives, records a
heartbeat/status file, and stops a silent or over-budget command so the agent
can diagnose it instead of issuing identical follow-up polls.
"""

from __future__ import annotations

import argparse
import json
import os
import selectors
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


EXIT_TIMEOUT = 124
EXIT_NO_PROGRESS = 125
EXIT_LAUNCH = 126


def _write_status(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _terminate(process: subprocess.Popen[bytes], *, grace_seconds: float = 0.5) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + grace_seconds
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.02)
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run(args: argparse.Namespace) -> int:
    cwd = args.cwd.expanduser().resolve()
    output_file = args.output_file.expanduser().resolve()
    status_file = args.status_file.expanduser().resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.parent.mkdir(parents=True, exist_ok=True)

    command = list(args.command)
    if not command:
        print("FAIL: command is required after --", file=sys.stderr)
        return EXIT_LAUNCH

    started_at = time.time()
    started_clock = time.monotonic()
    last_progress = started_clock
    heartbeat_count = 0
    byte_count = 0
    status: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "command": command,
        "cwd": str(cwd),
        "started_at": started_at,
        "heartbeat_at": started_at,
        "heartbeat_count": 0,
        "output_bytes": 0,
        "exit_code": None,
        "reason": None,
    }
    _write_status(status_file, status)

    try:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except (OSError, ValueError) as error:
        status.update(
            status="launch_failed",
            exit_code=EXIT_LAUNCH,
            reason=str(error),
            finished_at=time.time(),
        )
        _write_status(status_file, status)
        print(f"FAIL: unable to launch command: {error}", file=sys.stderr)
        return EXIT_LAUNCH

    selector = selectors.DefaultSelector()
    assert process.stdout is not None
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        with output_file.open("wb") as output:
            while True:
                now = time.monotonic()
                elapsed = now - started_clock
                if elapsed >= args.timeout_seconds:
                    _terminate(process)
                    status.update(
                        status="timeout",
                        exit_code=EXIT_TIMEOUT,
                        reason=f"timeout after {args.timeout_seconds:g}s",
                    )
                    print(f"BLOCKED: command timeout after {args.timeout_seconds:g}s", flush=True)
                    break
                if now - last_progress >= args.no_progress_seconds and process.poll() is None:
                    _terminate(process)
                    status.update(
                        status="blocked_no_progress",
                        exit_code=EXIT_NO_PROGRESS,
                        reason=f"no progress for {args.no_progress_seconds:g}s",
                    )
                    print(
                        f"BLOCKED: command made no progress for {args.no_progress_seconds:g}s",
                        flush=True,
                    )
                    break

                heartbeat_count += 1
                status.update(
                    heartbeat_at=time.time(),
                    heartbeat_count=heartbeat_count,
                    output_bytes=byte_count,
                    elapsed_seconds=elapsed,
                )
                _write_status(status_file, status)

                wait_for = min(args.poll_seconds, args.timeout_seconds - elapsed)
                events = selector.select(max(wait_for, 0.01))
                for key, _ in events:
                    chunk = key.fileobj.read1(65536)  # type: ignore[attr-defined]
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    output.write(chunk)
                    output.flush()
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                    byte_count += len(chunk)
                    last_progress = time.monotonic()

                if process.poll() is not None and not selector.get_map():
                    break

            # Drain any bytes emitted just before process termination.
            if selector.get_map():
                for key, _ in selector.select(0):
                    chunk = key.fileobj.read()  # type: ignore[attr-defined]
                    if chunk:
                        output.write(chunk)
                        output.flush()
                        sys.stdout.buffer.write(chunk)
                        sys.stdout.buffer.flush()
                        byte_count += len(chunk)
                selector.close()
    finally:
        try:
            selector.close()
        except Exception:
            pass

    if status["status"] == "running":
        return_code = process.wait()
        status.update(
            status="passed" if return_code == 0 else "failed",
            exit_code=return_code,
            reason=None if return_code == 0 else f"command exited with {return_code}",
        )
        result = return_code
    else:
        result = int(status["exit_code"])
    status.update(
        heartbeat_at=time.time(),
        heartbeat_count=heartbeat_count,
        output_bytes=byte_count,
        elapsed_seconds=time.monotonic() - started_clock,
        finished_at=time.time(),
    )
    _write_status(status_file, status)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--no-progress-seconds", type=float, default=300.0)
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--status-file", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    if args.timeout_seconds <= 0 or args.no_progress_seconds <= 0 or args.poll_seconds <= 0:
        parser.error("timeout, no-progress, and poll intervals must be positive")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
