#!/usr/bin/env python3
"""Validate real iOS capability decisions and runtime evidence."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
STATUSES={"Selected","Implemented","Runtime verified","Declined fallback","Not appropriate"}
REQUIRED=("capability","real_tool_or_sdk","version","license/source","actual_consumer","fallback","runtime_evidence","formula_record","status")
def validate(root: Path):
    path=root/".codex-work/capability-matrix.json"
    if not path.is_file(): return {"status":"Not verified","errors":["missing .codex-work/capability-matrix.json"]}
    try: data=json.loads(path.read_text(encoding="utf-8"))
    except Exception as e: return {"status":"Failed","errors":[f"invalid capability matrix JSON: {e}"]}
    rows=data.get("capabilities") if isinstance(data,dict) else None; errors=[]
    if not isinstance(rows,list) or not rows: errors.append("capabilities must be a non-empty list"); rows=[]
    for i,row in enumerate(rows):
        if not isinstance(row,dict): errors.append(f"capabilities[{i}] must be an object"); continue
        for f in REQUIRED:
            if f not in row: errors.append(f"capabilities[{i}] missing {f}")
        status=row.get("status")
        if status not in STATUSES: errors.append(f"capabilities[{i}] has invalid status")
        if status in {"Selected","Implemented","Runtime verified"}:
            for f in ("real_tool_or_sdk","version","license/source","actual_consumer"):
                if not isinstance(row.get(f),str) or not row[f].strip(): errors.append(f"capabilities[{i}] requires non-empty {f}")
            if not isinstance(row.get("runtime_evidence"),list) or not row.get("runtime_evidence"): errors.append(f"capabilities[{i}] requires runtime_evidence")
            if not isinstance(row.get("formula_record"),dict): errors.append(f"capabilities[{i}] requires formula_record")
            if isinstance(row.get("actual_consumer"),str) and row["actual_consumer"].strip().lower() in {"package","pubspec","dependency","installed"}: errors.append(f"capabilities[{i}] package-only consumer is not valid")
        if status=="Declined fallback" and not row.get("fallback"): errors.append(f"capabilities[{i}] declined rows require fallback")
        if status=="Not appropriate" and not row.get("decision_reason"): errors.append(f"capabilities[{i}] not-appropriate rows require decision_reason")
    return {"status":"Failed" if errors else "Passed","errors":errors,"count":len(rows)}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--project-root",required=True,type=Path); a=p.parse_args(); r=validate(a.project_root); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r["status"]=="Passed" else 1
if __name__=="__main__": sys.exit(main())
