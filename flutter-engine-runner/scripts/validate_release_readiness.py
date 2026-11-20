#!/usr/bin/env python3
"""Aggregate gate results into a machine-readable release-readiness decision."""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
ALLOWED={"Passed","Failed","Blocked","Not verified","Not applicable"}
def validate(root: Path):
    path=root/".codex-work/release-readiness.json"
    if not path.is_file(): return {"release_readiness":"Not verified","status":"Not verified","errors":["missing .codex-work/release-readiness.json"]}
    try: data=json.loads(path.read_text(encoding="utf-8"))
    except Exception as e: return {"release_readiness":"Not ready","status":"Failed","errors":[f"invalid readiness JSON: {e}"]}
    errors=[]
    if not isinstance(data.get("generated_at"), str) or not data.get("generated_at").strip():
        errors.append("generated_at must be a non-empty ISO-8601 timestamp")
    else:
        try:
            generated=datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
            if generated.tzinfo is None: errors.append("generated_at must include a timezone")
            elif generated.astimezone(timezone.utc) > datetime.now(timezone.utc).astimezone(timezone.utc): errors.append("generated_at is in the future")
        except ValueError: errors.append("generated_at is not valid ISO-8601")
    gates=data.get("gates") if isinstance(data,dict) else None
    if not isinstance(gates,list) or not gates: errors.append("gates must be a non-empty list"); gates=[]
    names=set()
    for i,g in enumerate(gates):
        if not isinstance(g,dict): errors.append(f"gates[{i}] must be an object"); continue
        for f in ("name","status","evidence"):
            if f not in g: errors.append(f"gates[{i}] missing {f}")
        if g.get("name") in names: errors.append(f"duplicate gate: {g.get('name')}")
        names.add(g.get("name"))
        if g.get("status") not in ALLOWED: errors.append(f"gates[{i}] has invalid status")
        if not isinstance(g.get("evidence"),list) or not g.get("evidence") or any(not isinstance(item,str) or not item.strip() for item in g.get("evidence", [])): errors.append(f"gates[{i}] evidence must contain non-empty paths")
        if g.get("status") in {"Failed","Blocked"} and not g.get("blocker"): errors.append(f"gates[{i}] failed/blocked gate requires blocker")
    required={"runtime","ios_artifacts","AppListing","quality_records","asset_staging","generation_cleanup","logo_quality","final_visual_product","git_handoff"}; missing=sorted(required-names)
    if missing: errors.append("missing required release gates: "+", ".join(missing))
    blockers=[g.get("name") for g in gates if isinstance(g,dict) and g.get("status") in {"Failed","Blocked"}]
    unresolved=[g.get("name") for g in gates if isinstance(g,dict) and g.get("status")=="Not verified"]
    declared=data.get("release_readiness")
    should="Ready for submission" if not errors and not blockers and not unresolved and all(g.get("status") in {"Passed","Not applicable"} for g in gates if isinstance(g,dict)) else "Not ready"
    if declared != should: errors.append(f"release_readiness must be {should!r} for the declared gate statuses")
    return {"release_readiness":"Not ready" if errors else should,"status":"Failed" if errors else "Passed","errors":errors,"blockers":blockers,"not_verified":unresolved,"gate_count":len(gates)}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--project-root",required=True,type=Path); a=p.parse_args(); r=validate(a.project_root); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r["status"]=="Passed" else 1
if __name__=="__main__": sys.exit(main())
