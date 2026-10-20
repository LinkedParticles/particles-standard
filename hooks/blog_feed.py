# SPDX-FileCopyrightText: 2026 The Particles authors
#
# SPDX-License-Identifier: Apache-2.0

"""mkdocs build hook — the front door's dev blog: its launch gate and its RSS feed.

The blog at ``https://linkedparticles.org/blog/`` is Material's built-in
``blog`` plugin. This hook adds the two things that plugin does not do.

**The gate.** The blog is banked before it is announced: posts are written and
reviewed in the tree, but the published site must not reveal that a blog
exists until the owner announces it. The plugin cannot be asked for that on its
own. Its drafts are already left out of ``mkdocs build``, but it always builds
the blog's index page (creating one if it is missing), and that page lands in
``sitemap.xml`` and the search index whether or not the nav links it. So the
blog is **live exactly when the site's nav names** ``blog/index.md``. Until then
this hook switches the plugin off and excludes everything under ``blog/``, and
the build carries no trace of it: no page, no feed, no sitemap row, no head
link. Adding the one nav line is the whole launch.

**The feed.** ``mkdocs-rss-plugin`` was the obvious choice and is not used, for
two reasons. Material's ``base.html`` advertises an RSS feed in the head of
every page whenever a plugin named ``rss`` is configured, and that plugin keeps
itself registered when ``enabled: false`` (it declares its own ``enabled``
option, so mkdocs's generic disable never applies), so a banked feed could not
be hidden. It would also bring GitPython, requests and CacheControl into a site
build that pins two packages, and its releases from 1.18.0 on depend on a fork
of mkdocs itself. An RSS 2.0 channel is small, so this hook writes it with the
standard library.

The feed is ``blog/feed.xml``. Every URL in it is absolute, built from
``site_url``, and each item carries the post's title, its front-matter
``description``, its date, and its authors' names. A published post with no
description or no author fails the build rather than shipping an item without
one. ``lastBuildDate`` is the newest post's date, not the clock, so two builds
of one tree write the same bytes.

**Preview.** ``PARTICLES_BLOG_PREVIEW=true`` in the environment treats the
blog as live and renders drafts too, so a
strict build checks the banked posts and their feed before anything is
announced::

    PARTICLES_BLOG_PREVIEW=true mkdocs build --strict
    PARTICLES_BLOG_PREVIEW=true mkdocs serve

A preview build is for checking only; it is never deployed. The switch is read
from the environment here rather than through mkdocs's ``!ENV`` tag, which the
repository's YAML check cannot parse.
"""

from __future__ import annotations

import datetime as dt
import email.utils
import logging
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

from mkdocs.exceptions import PluginError
from mkdocs.plugins import event_priority
from mkdocs.structure.files import InclusionLevel

log = logging.getLogger("mkdocs.hooks.blog_feed")

BLOG_DIR = "blog"
BLOG_INDEX = f"{BLOG_DIR}/index.md"
POSTS_PREFIX = f"{BLOG_DIR}/posts/"
FEED_PATH = f"{BLOG_DIR}/feed.xml"
BLOG_PLUGIN = "material/blog"

FEED_TITLE = "Particles blog"
FEED_DESCRIPTION = (
    "Notes from building Particles, an open ledger for what an AI agent "
    "believes: what was tested, what failed, and what changed."
)

_DC = "http://purl.org/dc/elements/1.1/"
_ATOM = "http://www.w3.org/2005/Atom"


@dataclass(frozen=True)
class FeedItem:
    """One published post, as the feed carries it."""

    title: str
    url: str
    description: str
    published: dt.datetime
    authors: tuple[str, ...]


# Per-build state. mkdocs loads a hook module once per process, and `serve`
# rebuilds in the same process, so `on_config` resets both on every build.
_live = False
_items: list[FeedItem] = []


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
def nav_names_blog(nav: Any) -> bool:
    """Whether a raw mkdocs ``nav`` value has an entry pointing at the blog index."""
    if isinstance(nav, str):
        return nav.strip("/") in (BLOG_INDEX, BLOG_DIR, f"{BLOG_DIR}/")
    if isinstance(nav, Mapping):
        return any(nav_names_blog(v) for v in nav.values())
    if isinstance(nav, Iterable):
        return any(nav_names_blog(v) for v in nav)
    return False


def post_date(value: Any) -> dt.datetime:
    """A post's front-matter ``date`` as an aware UTC datetime.

    Accepts the forms the blog plugin accepts: a date, a datetime, or a mapping
    whose ``created`` key holds one.
    """
    if isinstance(value, Mapping):
        value = value.get("created")
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt.UTC)
    if isinstance(value, dt.date):
        return dt.datetime(value.year, value.month, value.day, tzinfo=dt.UTC)
    raise PluginError(f"blog post date {value!r} is not a date")


def render_feed(items: Iterable[FeedItem], site_url: str) -> bytes:
    """An RSS 2.0 channel for ``items``, newest first, every URL absolute."""
    ET.register_namespace("dc", _DC)
    ET.register_namespace("atom", _ATOM)
    ordered = sorted(items, key=lambda i: (i.published, i.url), reverse=True)

    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = urljoin(site_url, f"{BLOG_DIR}/")
    ET.SubElement(channel, "description").text = FEED_DESCRIPTION
    ET.SubElement(channel, "language").text = "en"
    ET.SubElement(
        channel,
        f"{{{_ATOM}}}link",
        {"href": urljoin(site_url, FEED_PATH), "rel": "self", "type": "application/rss+xml"},
    )
    if ordered:
        newest = email.utils.format_datetime(ordered[0].published, usegmt=True)
        ET.SubElement(channel, "lastBuildDate").text = newest

    for item in ordered:
        node = ET.SubElement(channel, "item")
        ET.SubElement(node, "title").text = item.title
        ET.SubElement(node, "link").text = item.url
        ET.SubElement(node, "guid", {"isPermaLink": "true"}).text = item.url
        ET.SubElement(node, "description").text = item.description
        ET.SubElement(node, "pubDate").text = email.utils.format_datetime(
            item.published, usegmt=True
        )
        for author in item.authors:
            ET.SubElement(node, f"{{{_DC}}}creator").text = author

    ET.indent(rss)
    return ET.tostring(rss, encoding="utf-8", xml_declaration=True) + b"\n"


def _author_names(page: Any) -> tuple[str, ...]:
    # The blog plugin resolves each front-matter author id against the authors
    # file and attaches the result to the page; fall back to the raw ids.
    resolved = [getattr(a, "name", None) for a in getattr(page, "authors", None) or []]
    names = tuple(n for n in resolved if n)
    return names or tuple(str(a) for a in page.meta.get("authors") or [])


# --------------------------------------------------------------------------- #
# mkdocs events
# --------------------------------------------------------------------------- #
@event_priority(100)  # before the blog plugin's own on_config
def on_config(config: Any) -> Any:
    global _live
    _items.clear()
    preview = os.environ.get("PARTICLES_BLOG_PREVIEW", "").lower() in ("1", "true", "yes")
    _live = preview or nav_names_blog(config["nav"])

    plugin = config["plugins"].get(BLOG_PLUGIN)
    if plugin is not None:
        if not _live:
            plugin.config.enabled = False
        elif preview:
            plugin.config.draft = True  # render drafts so --strict checks them

    if _live:
        config["extra"]["blog_feed"] = FEED_PATH
    else:
        config["extra"].pop("blog_feed", None)
        log.info("blog is banked (no nav entry names %s); leaving it out of the build", BLOG_INDEX)
    return config


def on_files(files: Any, config: Any) -> Any:
    if not _live:
        for file in files:
            if file.src_uri.startswith(f"{BLOG_DIR}/"):
                file.inclusion = InclusionLevel.EXCLUDED
    return files


def on_page_context(context: Any, page: Any, config: Any, nav: Any) -> Any:
    if not _live or not page.file.src_uri.startswith(POSTS_PREFIX):
        return context
    where = page.file.src_uri
    description = page.meta.get("description")
    if not description:
        raise PluginError(f"blog post {where} has no front-matter description")
    authors = _author_names(page)
    if not authors:
        raise PluginError(f"blog post {where} names no author")
    _items.append(
        FeedItem(
            title=page.meta.get("title") or page.title,
            url=urljoin(config["site_url"], page.url),
            description=str(description).strip(),
            published=post_date(page.meta.get("date")),
            authors=authors,
        )
    )
    return context


def on_post_build(config: Any) -> None:
    if not _live:
        return
    if not config["site_url"]:
        raise PluginError("the blog feed needs site_url for its absolute URLs")
    out = Path(config["site_dir"]) / FEED_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(render_feed(_items, config["site_url"]))
    log.info("blog feed: %d item(s) at %s", len(_items), FEED_PATH)
