#!/usr/bin/env python3
"""Validate the final aduit delivery allowlist and screenshot dimensions."""
from __future__ import annotations
import argparse, json, struct, sys
from pathlib import Path
TOP={"intro.md","welcome.html","imgs","site","review"}; SITE={"index.html","PrivacyPolicy.html","Terms&Conditions.html","Support.html","img"}
def png_size(path: Path):
    data=path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data)<24: return None
    return struct.unpack(">II",data[16:24])
def validate(root: Path, *, final=False):
    aduit=root/"aduit"; errors=[]
    if not aduit.is_dir() or aduit.is_symlink(): return {"status":"Not verified","errors":["aduit/ is missing"]}
    actual={p.name for p in aduit.iterdir()}; extra=sorted(actual-TOP)
    if extra: errors.append("aduit contains unapproved entries: "+", ".join(extra))
    site=aduit/"site"
    if not site.is_dir() or site.is_symlink(): errors.append("aduit/site is missing or a symlink")
    else:
        site_actual={p.name for p in site.iterdir()}
        if site_actual-SITE: errors.append("site contains unapproved entries: "+", ".join(sorted(site_actual-SITE)))
        for name in ("PrivacyPolicy.html","Terms&Conditions.html","Support.html"):
            if not (site/name).is_file(): errors.append(f"missing policy page: {name}")
        site_index=site/"index.html"
        welcome=aduit/"welcome.html"
        if not site_index.is_file() or site_index.is_symlink():
            errors.append("site/index.html must be a regular copy of aduit/welcome.html")
        elif not welcome.is_file() or welcome.is_symlink():
            errors.append("aduit/welcome.html is required for the site/index.html copy")
        else:
            try:
                if site_index.read_bytes() != welcome.read_bytes():
                    errors.append("site/index.html must be byte-identical to aduit/welcome.html")
            except OSError as error:
                errors.append(f"cannot compare site/index.html and aduit/welcome.html: {error}")
        logo=site/"img/logo.png"
        if not logo.is_file() or logo.is_symlink(): errors.append("site/img/logo.png is missing or invalid")
    for path in aduit.rglob("*"):
        if path.is_symlink(): errors.append(f"symlink is not allowed: {path.relative_to(root)}")
        if path.name=="index.html" and path.parent != aduit/"site":
            errors.append(f"index.html is only allowed as aduit/site/index.html: {path.relative_to(root)}")
    imgs=aduit/"imgs"
    if not imgs.exists():
        if final: errors.append("aduit/imgs is required for final delivery")
    elif not imgs.is_dir() or imgs.is_symlink(): errors.append("aduit/imgs must be a regular directory")
    else:
        files=sorted(p for p in imgs.iterdir() if p.is_file())
        if final and len(files)!=5: errors.append(f"final aduit/imgs must contain exactly five PNGs, found {len(files)}")
        if any(p.suffix.lower()!=".png" for p in files): errors.append("aduit/imgs may contain PNG files only")
        if final:
            for p in files:
                size=png_size(p)
                if size!=(1206,2622): errors.append(f"{p.relative_to(root)} must be 1206x2622 PNG, got {size}")
    return {"status":"Failed" if errors else "Passed","errors":errors,"top_level":sorted(actual)}
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--project-root",required=True,type=Path); p.add_argument("--final",action="store_true"); a=p.parse_args(); r=validate(a.project_root,final=a.final); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r["status"]=="Passed" else 1
if __name__=="__main__": sys.exit(main())
