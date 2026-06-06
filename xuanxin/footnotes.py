"""Footnote ordering helpers."""

from __future__ import annotations

import re

FOOTNOTE_BLOCK_RE = re.compile(
    r'<div class="footnote">\s*.*?</div>',
    re.DOTALL | re.IGNORECASE,
)

CHAPTER_POSTER_RE = re.compile(
    r'<div class="xuanxin-pagebreak"[^>]*></div>\s*'
    r'<p>\s*<div class="fullpage-image"><img\b[^>]*\bsrc="[^"]*p\.jpg"[^>]*/>\s*</div>\s*</p>',
    re.DOTALL | re.IGNORECASE,
)


def reorder_footnotes_before_chapter_poster(html: str) -> str:
    """Move footnotes before the chapter-end ``p.jpg`` fullpage poster block."""
    footnote_match = FOOTNOTE_BLOCK_RE.search(html)
    poster_match = CHAPTER_POSTER_RE.search(html)
    if not footnote_match or not poster_match:
        return html

    if footnote_match.start() < poster_match.start():
        return html

    footnote_html = footnote_match.group(0)
    without_footnotes = html[: footnote_match.start()] + html[footnote_match.end() :]

    poster_match = CHAPTER_POSTER_RE.search(without_footnotes)
    if not poster_match:
        return html

    insert_at = poster_match.start()
    return (
        without_footnotes[:insert_at]
        + footnote_html
        + without_footnotes[insert_at:]
    )
