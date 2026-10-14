#!/usr/bin/env python3
"""Lightweight site check: builds with Jekyll, then verifies internal links in _site.

Usage: python3 bin/check_site.py
No third-party dependencies.
"""
import html
import pathlib
import re
import subprocess
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"


def build():
    print("Running jekyll build ...")
    r = subprocess.run(
        ["bundle", "exec", "jekyll", "build"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(r.stdout + r.stderr)
        sys.exit("jekyll build failed")
    for line in (r.stdout + r.stderr).splitlines():
        if "YAML Exception" in line or "Error" in line:
            sys.exit("build warning/error:\n" + line)
    print("build OK")


def check_internal_links():
    broken = []
    checked = 0
    for f in SITE.rglob("*.html"):
        rel = f.relative_to(SITE)
        text = f.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'(?:href|src)="([^"]+)"', text):
            url = urllib.parse.unquote(html.unescape(m.group(1)).strip())
            if url.startswith(("mailto:", "#", "data:", "http")):
                continue
            path = url.split("#")[0].split("?")[0]
            if not path:
                continue
            if not path.startswith("/"):  # relative to the page directory
                path = str(rel.parent / path)
            target = SITE / path.lstrip("/")
            if not any(
                c.exists()
                for c in (target, target / "index.html", pathlib.Path(str(target) + ".html"))
            ):
                broken.append(f"{rel}: -> {url}")
            else:
                checked += 1
    print(f"internal links OK: {checked}, broken: {len(broken)}")
    for b in broken:
        print("  BROKEN", b)
    return not broken


if __name__ == "__main__":
    build()
    ok = check_internal_links()
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
