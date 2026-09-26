"""Inline Markdown for titles pulled from the first H1 or frontmatter.

Titles bypass the Markdown pipeline, so `*They*` would render literally. Only a
small, predictable subset is supported: `code`, **strong**, *em*. Block syntax
(lists, headings) is deliberately ignored — a title like `1. Foo` stays text.
"""

from __future__ import annotations

import html
import re

from markupsafe import Markup

_CODE_RE = re.compile(r"`([^`]+)`")
_STRONG_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_EM_RE = re.compile(r"(?<!\*)\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?!\*)")
_TAG_RE = re.compile(r"<[^>]+>")


def title_html(text: str | None) -> Markup:
    """Escape *text* and render inline code/strong/em as HTML."""
    if not text:
        return Markup("")
    escaped = html.escape(str(text), quote=False)
    codes: list[str] = []

    def _stash(match: re.Match[str]) -> str:
        codes.append(f"<code>{match.group(1)}</code>")
        return f"\x00{len(codes) - 1}\x00"

    out = _CODE_RE.sub(_stash, escaped)
    out = _STRONG_RE.sub(r"<strong>\1</strong>", out)
    out = _EM_RE.sub(r"<em>\1</em>", out)
    out = re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], out)
    return Markup(out)


def title_plain(text: str | None) -> str:
    """Title with inline Markdown markers removed, for <title>/alt/JSON."""
    if not text:
        return ""
    return html.unescape(_TAG_RE.sub("", str(title_html(text))))
