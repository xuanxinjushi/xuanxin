"""GALLERYS/GALLERYE image carousel sections (bubble-compatible)."""

from __future__ import annotations

import html
import re
from collections.abc import Callable

_START_RE = re.compile(r"^>\s*GALLERYS\s*$")
_END_RE = re.compile(r"^>\s*GALLERYE\s*$")
_IMAGE_LINE_RE = re.compile(r"^>?\s*(!\[[^\]]*\]\([^)]+\)(?:\{[^}]*\})?)\s*$")
_IMAGE_PARTS_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_P_WRAP_RE = re.compile(r"^<p>\s*(.*)\s*</p>\s*$", re.DOTALL)


def _normalize_slide_html(html_fragment: str) -> str:
    html_fragment = html_fragment.strip()
    match = _P_WRAP_RE.match(html_fragment)
    if match:
        return match.group(1).strip()
    return html_fragment


def _parse_image_markdown(img_md: str) -> tuple[str, str]:
    match = _IMAGE_PARTS_RE.search(img_md)
    if not match:
        return "", img_md.strip()
    return match.group(1).strip(), match.group(2).strip()


def _build_slide(img_md: str, render_md: Callable[[str], str]) -> str:
    caption, _src = _parse_image_markdown(img_md)
    img_html = _normalize_slide_html(render_md(img_md))
    if caption:
        safe_caption = html.escape(caption, quote=True)
        return (
            f'<figure class="xuanxin-gallery-slide" data-caption="{safe_caption}">'
            f"{img_html}</figure>"
        )
    return f'<figure class="xuanxin-gallery-slide">{img_html}</figure>'


def _build_carousel(slides: list[str], *, has_captions: bool) -> str:
    total = len(slides)
    track = "".join(slides)
    caption_bar = ""
    if has_captions:
        caption_bar = (
            '  <button type="button" class="xuanxin-gallery-caption" hidden '
            'data-gallery-caption-bar aria-expanded="false"></button>\n'
        )
    return (
        f'<div class="xuanxin-gallery{" xuanxin-gallery-has-captions" if has_captions else ""}" '
        'data-gallery>\n'
        '  <div class="xuanxin-gallery-viewport">\n'
        f'    <div class="xuanxin-gallery-track">{track}</div>\n'
        "  </div>\n"
        f"{caption_bar}"
        '  <div class="xuanxin-gallery-controls">\n'
        '    <button type="button" class="xuanxin-gallery-btn xuanxin-gallery-prev" '
        'data-gallery-prev aria-label="Previous image">←</button>\n'
        f'    <span class="xuanxin-gallery-indicator" data-gallery-indicator>1 / {total}</span>\n'
        '    <button type="button" class="xuanxin-gallery-btn xuanxin-gallery-next" '
        'data-gallery-next aria-label="Next image">→</button>\n'
        "  </div>\n"
        "</div>"
    )


def process_gallery_sections(content: str, render_md: Callable[[str], str]) -> str:
    """Replace GALLERYS/GALLERYE blocks with a horizontal image carousel."""
    lines = content.splitlines(keepends=True)
    out: list[str] = []
    i = 0

    while i < len(lines):
        stripped = lines[i].rstrip("\r\n")
        if not _START_RE.match(stripped):
            out.append(lines[i])
            i += 1
            continue

        i += 1
        image_lines: list[str] = []
        while i < len(lines):
            line = lines[i]
            stripped = line.rstrip("\r\n")
            if _END_RE.match(stripped):
                i += 1
                break
            match = _IMAGE_LINE_RE.match(stripped)
            if match:
                image_lines.append(match.group(1))
            elif stripped.strip():
                image_lines.append(stripped.lstrip("> ").strip())
            i += 1

        if image_lines:
            slides = [_build_slide(img_md, render_md) for img_md in image_lines]
            has_captions = any(_parse_image_markdown(img_md)[0] for img_md in image_lines)
            out.append(_build_carousel(slides, has_captions=has_captions) + "\n\n")

    return "".join(out)
