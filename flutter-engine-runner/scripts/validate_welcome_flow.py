#!/usr/bin/env python3
"""Static Welcome/Initialization flow contract check."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

def validate(root: Path):
    errors=[]; welcome=root/"lib/welcome.dart"
    if not welcome.is_file(): return {"status":"Not verified","errors":["lib/welcome.dart is missing"]}
    source=welcome.read_text(encoding="utf-8",errors="replace")
    lib=root/"lib"; all_dart="\n".join(p.read_text(encoding="utf-8",errors="replace") for p in lib.rglob("*.dart"))
    if not re.search(r"class\s+WelcomePage\b",source): errors.append("WelcomePage must be defined in lib/welcome.dart")
    if not re.search(r"\bContinue\b",source): errors.append("Welcome must expose Continue")
    if re.search(r"\b(?:pause|paused|resume)\b|Pause|暂停",source,re.I): errors.append("Welcome pause controls or paused state must be removed")
    if re.search(r"(?:welcome|enter)\.html|aduit[/\\]",all_dart,re.I): errors.append("runtime Dart must not load delivery HTML or aduit paths")
    if re.search(r"GetX|Get\.to|Get\.off|GetMaterialApp|go_router|auto_route",all_dart): errors.append("Welcome flow must use Flutter Navigator, not GetX or external routing")
    if not re.search(r"Navigator(?:\.of\(context\)|State)|MaterialPageRoute|CupertinoPageRoute|PageRouteBuilder",all_dart): errors.append("native Navigator route is missing")
    has_clear=bool(re.search(r"Clear\s*Data|clearData|clear_data",all_dart,re.I)); has_entry=bool(re.search(r"/entry|Initialization|initialization",all_dart,re.I))
    if has_clear and has_entry and not re.search(r"(?:clearData|clear_data|Clear\s*Data)[\s\S]{0,700}(?:entry|Initialization|/entry)",all_dart,re.I): errors.append("Initialization must follow successful Clear Data")
    if has_entry and not re.search(r"\bEnter\b",all_dart): errors.append("Initialization action must be labelled Enter")
    for obsolete in (root/"welcome.html",root/"enter.html",root/"aduit/enter.html"):
        if obsolete.exists(): errors.append(f"obsolete Welcome HTML path exists: {obsolete.relative_to(root)}")
    if not (root/"aduit/welcome.html").is_file(): errors.append("standalone delivery aduit/welcome.html is missing")
    return {"status":"Failed" if errors else "Passed","errors":errors}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--project-root",required=True,type=Path); a=p.parse_args(); r=validate(a.project_root); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r["status"]=="Passed" else 1
if __name__=="__main__": sys.exit(main())
