#!/usr/bin/env python3
"""Validate resumable parallel execution state and heartbeat freshness."""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
STATUSES={"queued","running","passed","failed","blocked","skipped"}
def iso(value):
    if not isinstance(value,str): raise ValueError("timestamp must be ISO-8601")
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None: raise ValueError("timestamp must include timezone")
    return dt.astimezone(timezone.utc)
def validate(root: Path, *, now=None):
    path=root/".codex-work/execution-state.json"
    if not path.is_file(): return {"status":"Not verified","errors":["missing .codex-work/execution-state.json"]}
    try: data=json.loads(path.read_text(encoding="utf-8"))
    except Exception as e: return {"status":"Failed","errors":[f"invalid execution state JSON: {e}"]}
    errors=[]
    for f in ("schema_version","run_id","started_at","heartbeat_at","retry_count","tasks"):
        if f not in data: errors.append(f"missing {f}")
    if data.get("schema_version")!=1: errors.append("schema_version must be 1")
    if not isinstance(data.get("run_id"),str) or not data.get("run_id"): errors.append("run_id must be non-empty")
    current=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    try:
        start=iso(data.get("started_at")); hb=iso(data.get("heartbeat_at"))
        if hb<start: errors.append("heartbeat_at precedes started_at")
        if hb>current+timedelta(minutes=5): errors.append("heartbeat_at is in the future")
        if data.get("status")=="running" and current-hb>timedelta(minutes=10): errors.append("running execution heartbeat is stale")
    except Exception as e: errors.append(str(e))
    if not isinstance(data.get("retry_count"),int) or data.get("retry_count",-1)<0: errors.append("retry_count must be a non-negative integer")
    tasks=data.get("tasks")
    if not isinstance(tasks,list) or not tasks: errors.append("tasks must be a non-empty list")
    else:
        seen=set()
        for i,task in enumerate(tasks):
            if not isinstance(task,dict): errors.append(f"tasks[{i}] must be an object"); continue
            for f in ("id","status","started_at","heartbeat_at","retry_count","resume_action"):
                if f not in task: errors.append(f"tasks[{i}] missing {f}")
            if task.get("id") in seen: errors.append(f"duplicate task id: {task.get('id')}")
            seen.add(task.get("id"))
            if task.get("status") not in STATUSES: errors.append(f"tasks[{i}] has invalid status")
            if not isinstance(task.get("retry_count"),int) or task.get("retry_count",-1)<0: errors.append(f"tasks[{i}] retry_count must be non-negative")
            try:
                thb=iso(task.get("heartbeat_at"))
                if task.get("status")=="running" and current-thb>timedelta(minutes=10): errors.append(f"tasks[{i}] running heartbeat is stale")
            except Exception as e: errors.append(f"tasks[{i}]: {e}")
            if task.get("status")=="blocked" and not task.get("blocked_reason"): errors.append(f"tasks[{i}] blocked tasks require blocked_reason")
    return {"status":"Failed" if errors else "Passed","errors":errors}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--project-root",required=True,type=Path); a=p.parse_args(); r=validate(a.project_root); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r["status"]=="Passed" else 1
if __name__=="__main__": sys.exit(main())
