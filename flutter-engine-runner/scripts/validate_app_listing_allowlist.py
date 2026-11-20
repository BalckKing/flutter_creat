#!/usr/bin/env python3
"""Validate the final AppListing delivery allowlist.

Final delivery no longer requires a fixed screenshot count. Runtime visual
evidence remains in the project work records and is validated per page/state.
"""
from __future__ import annotations
import argparse, json, struct, sys
from pathlib import Path
TOP={"intro.md","welcome.html","imgs","site","review"}; SITE={"index.html","PrivacyPolicy.html","Terms&Conditions.html","Support.html","img"}
def png_size(path: Path):
    data=path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data)<24: return None
    return struct.unpack(">II",data[16:24])
def validate(root: Path, *, final=False):
    AppListing=root/"AppListing"; errors=[]
    if not AppListing.is_dir() or AppListing.is_symlink(): return {"status":"Not verified","errors":["AppListing/ is missing"]}
    actual={p.name for p in AppListing.iterdir()}; extra=sorted(actual-TOP)
    if extra: errors.append("AppListing contains unapproved entries: "+", ".join(extra))
    site=AppListing/"site"
    if not site.is_dir() or site.is_symlink(): errors.append("AppListing/site is missing or a symlink")
    else:
        site_actual={p.name for p in site.iterdir()}
        if site_actual-SITE: errors.append("site contains unapproved entries: "+", ".join(sorted(site_actual-SITE)))
        for name in ("PrivacyPolicy.html","Terms&Conditions.html","Support.html"):
            if not (site/name).is_file(): errors.append(f"missing policy page: {name}")
        site_index=site/"index.html"
        welcome=AppListing/"welcome.html"
        if not site_index.is_file() or site_index.is_symlink():
            errors.append("site/index.html must be a regular copy of AppListing/welcome.html")
        elif not welcome.is_file() or welcome.is_symlink():
            errors.append("AppListing/welcome.html is required for the site/index.html copy")
        else:
            try:
                if site_index.read_bytes() != welcome.read_bytes():
                    errors.append("site/index.html must be byte-identical to AppListing/welcome.html")
            except OSError as error:
                errors.append(f"cannot compare site/index.html and AppListing/welcome.html: {error}")
        logo=site/"img/logo.png"
        if not logo.is_file() or logo.is_symlink(): errors.append("site/img/logo.png is missing or invalid")
    for path in AppListing.rglob("*"):
        if path.is_symlink(): errors.append(f"symlink is not allowed: {path.relative_to(root)}")
        if path.name=="index.html" and path.parent != AppListing/"site":
            errors.append(f"index.html is only allowed as AppListing/site/index.html: {path.relative_to(root)}")
    imgs=AppListing/"imgs"
    if not imgs.exists():
        # The directory is optional now; the delivery allowlist does not force
        # screenshot capture or a fixed number of files.
        pass
    elif not imgs.is_dir() or imgs.is_symlink(): errors.append("AppListing/imgs must be a regular directory")
    else:
        files=sorted(p for p in imgs.iterdir() if p.is_file())
        if any(p.suffix.lower()!=".png" for p in files): errors.append("AppListing/imgs may contain PNG files only")
        if final:
            for p in files:
                if png_size(p) is None: errors.append(f"{p.relative_to(root)} must be a decodable PNG")
    return {"status":"Failed" if errors else "Passed","errors":errors,"top_level":sorted(actual)}
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--project-root",required=True,type=Path); p.add_argument("--final",action="store_true"); a=p.parse_args(); r=validate(a.project_root,final=a.final); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r["status"]=="Passed" else 1
if __name__=="__main__": sys.exit(main())
