#!/usr/bin/env python3
"""Lightweight docs + artifact check for the particles-standard repository.

Pure stdlib, no build step — the standard repo ships spec prose plus the
normative machine-readable artifacts, so this smoke check verifies two things a
reader depends on:

  1. Every JSON / JSON-LD artifact under `artifacts/` parses.
  2. Every relative Markdown link `[text](path)` under `docs/` resolves to a
     file that exists in the tree (anchors and external `http(s)://` / `mailto:`
     links are not followed).

Run from the repository root::

    python .github/docs_check.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# `[text](target)` — capture the target; skip images (`![alt](...)`) is not
# needed (an image link resolving is checked the same way).
_MD_LINK_RE = re.compile(r"(?<!\\)\[[^\]]*\]\(([^)]+)\)")


def check_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    art = root / "artifacts"
    if not art.is_dir():
        return errors
    for path in sorted(art.rglob("*")):
        if path.suffix.lower() not in {".json", ".jsonld"}:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"{path.relative_to(root)}: invalid JSON ({exc})")
    return errors


def check_doc_links(root: Path) -> list[str]:
    errors: list[str] = []
    docs = root / "docs"
    if not docs.is_dir():
        return errors
    for md in sorted(docs.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        for target in _MD_LINK_RE.findall(text):
            target = target.strip()
            # Skip external, anchor-only, and mail links.
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            # Drop any in-page anchor / query suffix before resolving the path.
            rel = target.split("#", 1)[0].split("?", 1)[0]
            if not rel:
                continue
            resolved = (md.parent / rel).resolve()
            if not resolved.exists():
                errors.append(f"{md.relative_to(root)}: broken link -> {target}")
    return errors


def main() -> int:
    root = Path.cwd()
    errors = check_artifacts(root) + check_doc_links(root)
    if errors:
        print("docs check: FAIL", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    print("docs check: OK (artifacts parse; relative doc links resolve).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
