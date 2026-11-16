#!/usr/bin/env python3
"""CI: verify that every local link and image referenced by the pages actually exists."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".edgeprofile", "node_modules", "tools", "__pycache__"}

errors = []
pages = 0
checked = 0

for html in ROOT.rglob("*.html"):
    if any(part in SKIP_DIRS for part in html.relative_to(ROOT).parts):
        continue
    pages += 1
    text = html.read_text(encoding="utf-8", errors="replace")
    refs = re.findall(r'(?:src|href)="([^"]+)"', text)
    for ref in refs:
        if ref.startswith(("http://", "https://", "#", "mailto:", "javascript:")):
            continue
        if ref.startswith("data:"):
            continue
        target = (html.parent / ref.split("#")[0].split("?")[0]).resolve()
        checked += 1
        if not target.exists():
            errors.append(f"{html.relative_to(ROOT)}  ->  {ref}  (not found)")

print(f"pages checked : {pages}")
print(f"links checked : {checked}")

if errors:
    print(f"\nFAILED: {len(errors)} broken reference(s)")
    for e in errors:
        print("  -", e)
    sys.exit(1)

print("\nOK: all local references resolve")
