#!/usr/bin/env python3
"""Render the Particles design-system preview cards.

Reads ``tokens.css`` + ``components.css`` and each fragment in ``cards/``, and
writes one self-contained HTML file per card into ``previews/`` plus a single
``index.html`` overview. Self-contained matters: the Claude Design pane and the
Artifact viewer both block external requests, so every preview inlines its CSS.

Each fragment's first line is the card marker Claude Design reads to build its
card index, e.g. ``<!-- @dsCard group="Colors" name="Palette" -->``. The build
copies that line verbatim to line 1 of the rendered file. A fragment may carry
a second-line ``<!-- @layout single -->`` comment to opt out of the default
side-by-side light/dark rendering (used where the fragment already shows both).

Run from anywhere::

    uv run python design/build.py

stdlib only — no third-party imports.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARDS = HERE / "cards"
OUT = HERE / "previews"


def _block(css: str, opener: str) -> str:
    """Return the body of the first ``opener { … }`` block in ``css``."""
    start = css.index(opener)
    brace = css.index("{", start)
    depth, i = 0, brace
    while i < len(css):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return css[brace + 1 : i]
        i += 1
    raise ValueError(f"unterminated block for {opener!r}")


LIGHT_OPENER = ":root {\n  color-scheme: light;"
DARK_OPENER = ':root[data-theme="dark"] {'
SEMANTIC_OPENER = ":root, .p-theme-light, .p-theme-dark {"


def scoped_tokens(
    tokens: str, light_selector: str, dark_selector: str, *, with_semantic: bool = False
) -> str:
    """Re-scope the light / dark primitive blocks of tokens.css under two selectors.

    Used by the preview build (``.p-theme-light`` / ``.p-theme-dark`` panes) and by
    the mkdocs hook (``body[data-md-color-scheme=…]``, Material's own toggle). With
    ``with_semantic`` the semantic layer (``--p-status-*`` …) is repeated inside
    each scope, which is required whenever the scope is NOT ``:root``: a custom
    property resolves ``var()`` where it is declared, so a semantic token left on
    ``:root`` would keep pointing at ``:root``'s primitives, not the scope's.
    """
    light = _block(tokens, LIGHT_OPENER)
    dark = _block(tokens, DARK_OPENER)
    sem = _block(tokens, SEMANTIC_OPENER) if with_semantic else ""
    return f"{light_selector} {{{light}{sem}}}\n{dark_selector} {{{dark}{sem}}}\n"


def scoped_themes(tokens: str) -> str:
    """Derive ``.p-theme-light`` / ``.p-theme-dark`` scopes from tokens.css."""
    return scoped_tokens(tokens, ".p-theme-light", ".p-theme-dark")


PREVIEW_CSS = (HERE / "preview.css").read_text()  # preview chrome, not part of the system

MARKER = re.compile(r"<!--\s*@dsCard\s+(.*?)\s*-->")
ATTR = re.compile(r'(\w+)="([^"]*)"')


def render(fragment: str, tokens: str, components: str, scoped: str) -> tuple[str, dict[str, str]]:
    lines = fragment.splitlines()
    marker = lines[0].strip()
    m = MARKER.match(marker)
    if not m:
        raise ValueError("fragment must start with a @dsCard marker")
    attrs = dict(ATTR.findall(m.group(1)))
    body_lines = lines[1:]
    single = False
    if body_lines and body_lines[0].strip() == "<!-- @layout single -->":
        single = True
        body_lines = body_lines[1:]
    body = "\n".join(body_lines).strip("\n")
    if single:
        content = f'<div class="ds-single">\n{body}\n</div>'
    else:
        content = (
            '<div class="ds-panes">\n'
            '<div class="ds-pane p-theme-light"><p class="ds-pane--label">Light</p>\n'
            f"{body}\n</div>\n"
            '<div class="ds-pane p-theme-dark"><p class="ds-pane--label">Dark</p>\n'
            f"{body}\n</div>\n</div>"
        )
    title = attrs.get("name", "Particles design system")
    html = (
        f"{marker}\n"
        '<!doctype html>\n<html lang="en" class="p-root">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title} — Particles</title>\n"
        f"<style>\n{tokens}\n{scoped}\n{components}\n{PREVIEW_CSS}</style>\n</head>\n"
        f"<body>\n{content}\n</body>\n</html>\n"
    )
    return html, attrs | {"_content": content}


def main() -> int:
    tokens = (HERE / "tokens.css").read_text()
    components = (HERE / "components.css").read_text()
    scoped = scoped_themes(tokens)
    OUT.mkdir(exist_ok=True)
    index_parts: list[str] = []
    written: list[Path] = []
    for frag in sorted(CARDS.glob("*.html")):
        html, attrs = render(frag.read_text(), tokens, components, scoped)
        # strip the leading NN- ordering prefix for the public preview name
        name = re.sub(r"^\d+-", "", frag.stem)
        out = OUT / f"{name}.html"
        out.write_text(html)
        written.append(out)
        sub = attrs.get("subtitle", "")
        title = f"{attrs.get('group', '')} · {attrs.get('name', name)}"
        index_parts.append(
            '<section class="ds-index-card">'
            f'<div class="ds-index-title">{title}</div>'
            + (f'<div class="ds-index-sub">{sub}</div>' if sub else "")
            + f"{attrs['_content']}</section>"
        )
    index = (
        '<!doctype html>\n<html lang="en" class="p-root">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Particles Design System</title>\n"
        f"<style>\n{tokens}\n{scoped}\n{components}\n{PREVIEW_CSS}</style>\n</head>\n<body>\n"
        + "\n".join(index_parts)
        + "\n</body>\n</html>\n"
    )
    (HERE / "index.html").write_text(index)
    written.append(HERE / "index.html")
    for p in written:
        print(p.relative_to(HERE.parent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
