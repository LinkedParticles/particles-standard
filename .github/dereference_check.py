#!/usr/bin/env python3
"""Assert every canonical identifier this project publishes actually resolves.

Pure stdlib, no build step. Every particle serialized by a conforming
implementation carries absolute identifiers — each schema's ``$id``, the JSON-LD
``@context`` URL, the SHACL vocabulary namespace — pointing at
``https://linkedparticles.org``. Those strings are permanent: they are baked into
published data and cannot be swapped out later. So the site that serves them has
one obligation, and this script is the check on it. For every artifact in this
tree, and for the vocabulary page:

  1. the identifier resolves with HTTP 200;
  2. the media type is the one a consumer parses by;
  3. the served bytes are **identical** to the bytes in this tree.

(3) is the one that matters most and is the easiest to lose: a build step that
"helpfully" reformats JSON, or a host that rewrites a document, breaks hash
equality for every consumer that pinned the artifact — silently, because the
document still parses.

The base URL is taken from the artifacts themselves (``particle.schema.json``'s
own ``$id``), never configured here, so this check cannot drift from what the
published data actually claims. Override with ``--base-url`` to test a staging
deploy or a fork.

Run from the repository root::

    python .github/dereference_check.py
    python .github/dereference_check.py --base-url https://example.github.io
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

# Where the artifacts live in this tree, and the site path they are served at.
# The pairing is asserted by the site build; here it only forms the URL.
ARTIFACT_DIR = Path("artifacts/schemas")
SERVE_PREFIX = "schemas"
ORIGIN_ANCHOR = "particle.schema.json"

# The human vocabulary page: the `#`-fragment namespace every `particles:` term
# expands into. Fetched as a page, and checked for a term anchor — a 200 that
# does not actually carry the fragment target is not a resolved identifier.
VOCAB_PATH = "vocab"
VOCAB_SAMPLE_ANCHORS = ("Particle", "content", "confidence", "status", "supersedes")

# Media types accepted per suffix. GitHub Pages serves `.jsonld` as
# `application/ld+json` and `.ttl` as `text/turtle`; `.json` arrives as
# `application/json` rather than the `application/schema+json` a JSON Schema may
# also be served as, and Pages offers no media-type override. Both are accepted
# for `.json` so a future move to a host that can send the stricter type is not
# a breaking change here.
ACCEPTED_TYPES: dict[str, tuple[str, ...]] = {
    ".json": ("application/json", "application/schema+json"),
    ".jsonld": ("application/ld+json",),
    ".ttl": ("text/turtle",),
    ".md": ("text/markdown", "text/plain"),
    "": ("text/plain",),
}

TIMEOUT = 30
USER_AGENT = "particles-dereference-check/1.0 (+https://linkedparticles.org)"


def base_url_from_artifacts(root: Path) -> str:
    """The scheme + host the artifacts themselves claim to be published at."""
    src = root / ARTIFACT_DIR / ORIGIN_ANCHOR
    doc = json.loads(src.read_text(encoding="utf-8"))
    schema_id = doc.get("$id")
    if not isinstance(schema_id, str):
        raise SystemExit(f"{src}: no string `$id` to take the canonical origin from")
    parts = urlsplit(schema_id)
    if not parts.scheme or not parts.netloc:
        raise SystemExit(f"{src}: `$id` {schema_id!r} is not an absolute URL")
    return f"{parts.scheme}://{parts.netloc}"


def fetch(url: str) -> tuple[int, str, bytes]:
    """``(status, media_type, body)`` for *url*; status 0 on a transport failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310 - fixed https origin
            media = (resp.headers.get_content_type() or "").lower()
            return int(resp.status), media, resp.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), (exc.headers.get_content_type() or "").lower(), b""
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"    transport error: {exc}", file=sys.stderr)
        return 0, "", b""


def check_artifacts(root: Path, base: str) -> list[str]:
    """Fetch every artifact at its canonical identifier and compare bytes."""
    errors: list[str] = []
    art_root = root / ARTIFACT_DIR
    if not art_root.is_dir():
        return [f"{ARTIFACT_DIR} missing — nothing to check"]
    for path in sorted(p for p in art_root.rglob("*") if p.is_file()):
        rel = path.relative_to(art_root).as_posix()
        url = f"{base}/{SERVE_PREFIX}/{rel}"
        status, media, body = fetch(url)
        if status != 200:
            errors.append(f"{url}: HTTP {status or 'unreachable'} (expected 200)")
            continue
        accepted = ACCEPTED_TYPES.get(path.suffix.lower(), ())
        if accepted and media not in accepted:
            errors.append(f"{url}: media type {media!r}, expected one of {accepted}")
        local = path.read_bytes()
        if body != local:
            errors.append(
                f"{url}: served {len(body)} bytes, tree has {len(local)} "
                f"({ARTIFACT_DIR / rel}) — not byte-identical"
            )
        else:
            print(f"  ok  {url}  [{media}]  {len(body)} bytes")
    return errors


def check_vocab(base: str) -> list[str]:
    """Fetch the vocabulary page and confirm the term fragments are really there."""
    errors: list[str] = []
    url = f"{base}/{VOCAB_PATH}"
    status, media, body = fetch(url)
    if status != 200:
        return [f"{url}: HTTP {status or 'unreachable'} (expected 200)"]
    if not media.startswith("text/html"):
        errors.append(f"{url}: media type {media!r}, expected text/html")
    text = body.decode("utf-8", errors="replace")
    missing = [a for a in VOCAB_SAMPLE_ANCHORS if f'id="{a}"' not in text]
    if missing:
        errors.append(
            f"{url}: served page carries no anchor for {', '.join(missing)} — "
            "the `#`-fragment identifiers do not resolve to a target"
        )
    if not errors:
        print(f"  ok  {url}  [{media}]  {len(body)} bytes, term anchors present")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--base-url",
        help="Origin to check (default: the origin the artifacts' own `$id` names).",
    )
    args = ap.parse_args()

    root = Path.cwd()
    base = (args.base_url or base_url_from_artifacts(root)).rstrip("/")
    print(f"dereference check: {base}")

    errors = check_artifacts(root, base) + check_vocab(base)
    if errors:
        print("\ndereference check: FAIL", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        print(
            "\n  Published identifiers must resolve to these exact bytes. Check the "
            "Pages\n  deploy, the custom domain + certificate, and DNS.",
            file=sys.stderr,
        )
        return 1
    print("\ndereference check: OK (every canonical identifier resolves, byte-identical).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
