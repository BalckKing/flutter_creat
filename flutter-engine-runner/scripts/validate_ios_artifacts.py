#!/usr/bin/env python3
"""Check iOS source and built-artifact gates without claiming a build exists."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path
import plistlib
from typing import Any

ATT_MARKERS = ("NSUserTrackingUsageDescription", "ATTrackingManager", "AppTrackingTransparency", "ASIdentifierManager", "PERMISSION_APP_TRACKING_TRANSPARENCY=1", "advertisingIdentifier")
PHOTO_MARKER = "PERMISSION_PHOTOS=1"

def check(name: str, status: str, detail: str) -> dict[str, str]: return {"name": name, "status": status, "detail": detail}

def read_plist(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try: data = plistlib.loads(path.read_bytes())
    except (OSError, plistlib.InvalidFileException, ValueError) as error: return None, str(error)
    return (data, None) if isinstance(data, dict) else (None, "plist root must be a dictionary")

def ruby_error(path: Path) -> str | None:
    try: run = subprocess.run(["ruby", "-c", str(path)], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as error: return str(error)
    return None if run.returncode == 0 else (run.stderr.strip() or run.stdout.strip() or "ruby -c failed")

def validate(root: Path, *, photo_access: str = "none", artifact: Path | None = None) -> dict[str, Any]:
    root = root.resolve(); ios = root / "ios"; checks: list[dict[str, str]] = []; errors: list[str] = []
    if not ios.is_dir(): return {"status": "Not verified", "checks": [check("ios-source", "Not verified", "ios/ is missing")], "errors": ["ios/ is missing"]}
    info = ios / "Runner/Info.plist"
    if not info.is_file(): checks.append(check("Info.plist", "Failed", "ios/Runner/Info.plist is missing")); errors.append("Info.plist is missing")
    else:
        _, err = read_plist(info); checks.append(check("Info.plist", "Failed" if err else "Passed", err or str(info.relative_to(root))))
        if err: errors.append(f"Info.plist: {err}")
    framework = ios / "Flutter/AppFrameworkInfo.plist"
    if not framework.is_file(): checks.append(check("MinimumOSVersion source", "Failed", "AppFrameworkInfo.plist is missing")); errors.append("AppFrameworkInfo.plist is missing")
    else:
        data, err = read_plist(framework); minimum = data.get("MinimumOSVersion") if data else None
        ok = not err and isinstance(minimum, str) and re.fullmatch(r"\d+(?:\.\d+){1,2}", minimum)
        detail = minimum if ok else (err or "MinimumOSVersion is missing or invalid")
        checks.append(check("MinimumOSVersion source", "Passed" if ok else "Failed", detail))
        if not ok: errors.append(f"MinimumOSVersion source: {detail}")
    pubspec = root / "pubspec.yaml"; pub_text = pubspec.read_text(encoding="utf-8", errors="ignore") if pubspec.is_file() else ""
    pods_expected = (ios / "Pods").exists() or "permission_handler" in pub_text or "pod '" in (ios / "Podfile").read_text(encoding="utf-8", errors="ignore") if (ios / "Podfile").is_file() else (ios / "Pods").exists() or "permission_handler" in pub_text
    podfile = ios / "Podfile"
    if not podfile.is_file():
        status = "Failed" if pods_expected else "Not applicable"; checks.append(check("Podfile", status, "Podfile is missing" if status == "Failed" else "CocoaPods not indicated"))
        if status == "Failed": errors.append("Podfile is missing while CocoaPods is indicated")
    else:
        err = ruby_error(podfile); checks.append(check("Podfile", "Failed" if err else "Passed", err or str(podfile.relative_to(root))))
        if err: errors.append(f"Podfile: {err}")
    source_files = [p for p in ios.rglob("*") if p.is_file() and p.suffix.lower() in {".swift", ".m", ".mm", ".h", ".plist", ".pbxproj", ".podspec", ""}]
    source_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in source_files)
    att = sorted({marker for marker in ATT_MARKERS if marker in source_text}); checks.append(check("ATT removal", "Failed" if att else "Passed", ", ".join(att) if att else "no ATT markers found"))
    if att: errors.append("ATT markers remain: " + ", ".join(att))
    pod_text = podfile.read_text(encoding="utf-8", errors="ignore") if podfile.is_file() else ""
    if photo_access == "read-write":
        pod_files = [p for p in (ios / "Pods").rglob("*") if p.is_file()] if (ios / "Pods").exists() else []
        present = PHOTO_MARKER in pod_text or any(PHOTO_MARKER in p.read_text(encoding="utf-8", errors="ignore") for p in pod_files)
        checks.append(check("PERMISSION_PHOTOS=1", "Passed" if present else "Failed", PHOTO_MARKER if present else "required photo macro is missing"))
        if not present: errors.append("PERMISSION_PHOTOS=1 is missing for read-write photo access")
    else: checks.append(check("PERMISSION_PHOTOS=1", "Not applicable", f"photo access mode: {photo_access}"))
    if artifact is None: checks.append(check("built artifact", "Not verified", "no .app/Archive artifact supplied"))
    elif not artifact.exists(): checks.append(check("built artifact", "Failed", f"artifact does not exist: {artifact}")); errors.append("built artifact does not exist")
    else:
        candidates = list(artifact.rglob("AppFrameworkInfo.plist")); artifact_errors=[]
        for candidate in candidates:
            data, err = read_plist(candidate)
            if err: artifact_errors.append(f"{candidate}: {err}")
            elif not isinstance(data.get("MinimumOSVersion"), str): artifact_errors.append(f"{candidate}: MinimumOSVersion missing")
        ok = bool(candidates) and not artifact_errors; checks.append(check("built artifact", "Passed" if ok else "Failed", "artifact plist verified" if ok else "; ".join(artifact_errors) or "AppFrameworkInfo.plist not found")); errors.extend(artifact_errors)
    status = "Failed" if errors else ("Not verified" if any(c["status"] == "Not verified" for c in checks) else "Passed")
    return {"status": status, "checks": checks, "errors": errors}

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--project-root",required=True,type=Path); p.add_argument("--photo-access",choices=("none","picker","read-write","add-only"),default="none"); p.add_argument("--artifact",type=Path); a=p.parse_args(); r=validate(a.project_root,photo_access=a.photo_access,artifact=a.artifact); print(json.dumps(r,ensure_ascii=False,indent=2)); return {"Passed":0,"Failed":1,"Not verified":2}.get(r["status"],1)
if __name__ == "__main__": sys.exit(main())
