#!/usr/bin/env python3
"""Enforce the Developer Certificate of Origin (DCO) sign-off on PR commits.

This is a small, self-contained checker vendored into each public repository's
`.github/` directory. It has no third-party dependencies (pure stdlib) so the
CI workflow can run it directly with the runner's system Python. It mirrors the
private upstream's own sign-off gate, but is intentionally standalone: the
upstream's tooling directory is never part of a public export, so the public CI
cannot call into it.

Usage::

    python .github/dco_check.py --range <base>..<head>

Validate every non-merge commit in the range: each must carry a
`Signed-off-by: Name <email>` trailer whose email matches that commit's own
author email — i.e. what `git commit -s` produces.

Exempt (sign-off not required, matching the common DCO-bot behaviour):
  - merge commits (a merge has no single authoring contributor);
  - autosquash commits (`fixup!` / `squash!` / `amend!`), which fold into a
    signed-off target before landing;
  - bot authors: GitHub Apps author as `<id>+<app>[bot]@users.noreply.github.com`
    but can only sign off as `support@github.com`, so the author-email match can
    never hold. The DCO certifies human contribution; a bot bump is reviewed and
    merged by a human who carries the provenance.

This is an honour-system provenance gate, not a security control.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

_SIGNOFF_RE = re.compile(
    r"^Signed-off-by:\s+(?P<name>.+?)\s+<(?P<email>[^<>@\s]+@[^<>@\s]+)>\s*$",
    re.MULTILINE,
)
_AUTOSQUASH_RE = re.compile(r"^(fixup|squash|amend)! ", re.IGNORECASE)
_BOT_AUTHOR_SUFFIX = "[bot]@users.noreply.github.com"

_HOWTO = (
    "Add one with `git commit -s` (or `--signoff`), which appends:\n"
    "    Signed-off-by: Your Name <your.email@example.com>\n"
    "Fix an existing series with `git rebase --signoff <base>`.\n"
    "By signing off you certify the Developer Certificate of Origin (see the\n"
    "DCO file). There is no CLA. The name/email must be your real ones and\n"
    "match your git author identity (CONTRIBUTING.md)."
)


def _is_exempt(message: str) -> bool:
    subject = next((ln for ln in message.splitlines() if ln.strip()), "")
    return subject.startswith("Merge ") or bool(_AUTOSQUASH_RE.match(subject))


def _is_bot_author(email: str) -> bool:
    return email.lower().endswith(_BOT_AUTHOR_SUFFIX)


def _signoff_emails(message: str) -> list[str]:
    return [m.group("email").lower() for m in _SIGNOFF_RE.finditer(message)]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def check_range(rev_range: str) -> int:
    """Validate every non-merge commit in ``base..head`` (CI on a PR)."""
    shas = _git("rev-list", "--no-merges", rev_range).split()
    failures: list[str] = []
    for sha in shas:
        message = _git("show", "-s", "--format=%B", sha)
        if _is_exempt(message):
            continue
        author_email = _git("show", "-s", "--format=%ae", sha).lower()
        if _is_bot_author(author_email):
            continue
        if author_email not in _signoff_emails(message):
            subject = _git("show", "-s", "--format=%s", sha)
            failures.append(f"  {sha[:12]} {subject}  (author <{author_email}>)")

    if failures:
        print(
            "DCO: the following commit(s) lack a Signed-off-by matching their "
            "author:\n" + "\n".join(failures) + f"\n\n{_HOWTO}",
            file=sys.stderr,
        )
        return 1
    print(f"DCO: {len(shas)} commit(s) signed off.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--range", dest="rev_range", required=True, help="commit range base..head")
    args = parser.parse_args(argv)
    return check_range(args.rev_range)


if __name__ == "__main__":
    raise SystemExit(main())
