"""GALLERYS/GALLERYE image carousel sections (bubble-compatible)."""

from __future__ import annotations

import hashlib
import html
import re
from collections.abc import Callable
from pathlib import Path

_START_RE = re.compile(r"^>\s*GALLERYS(?:\s+password:\s*(.+))?\s*$", re.IGNORECASE)
_END_RE = re.compile(r"^>\s*GALLERYE\s*$")
_MEDIA_LINE_RE = re.compile(r"^>?\s*(!\[[^\]]*\]\([^)]+\)(?:\{[^}]*\})?)\s*$")
_MEDIA_PARTS_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_P_WRAP_RE = re.compile(r"^<p>\s*(.*)\s*</p>\s*$", re.DOTALL)
_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v", ".ogv"}


def _password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def password_hash(password: str) -> str:
    """Public SHA-256 hex digest for a diary/gallery password."""
    return _password_hash(password)


def _encrypt_media_tags(block: str) -> str:
    def repl_img(match: re.Match[str]) -> str:
        pre, src, post = match.group(1), match.group(2), match.group(3)
        enc = html.escape(f"{src}.enc", quote=True)
        return (
            f'<img{pre} class="xuanxin-encrypted-media" '
            f'data-encrypted-src="{enc}" data-media-kind="image" hidden{post}>'
        )

    def repl_video(match: re.Match[str]) -> str:
        pre, src, post = match.group(1), match.group(2), match.group(3)
        enc = html.escape(f"{src}.enc", quote=True)
        return (
            f'<video{pre} class="xuanxin-gallery-video xuanxin-encrypted-media" controls '
            'playsinline preload="metadata" '
            f'data-encrypted-src="{enc}" data-media-kind="video" hidden{post}></video>'
        )

    block = re.sub(r'<img\b([^>]*?)\ssrc="([^"]+)"([^>]*)>', repl_img, block)
    block = re.sub(
        r'<video\b([^>]*?)\ssrc="([^"]+)"([^>]*)></video>',
        repl_video,
        block,
    )
    return block


def _normalize_slide_html(html_fragment: str) -> str:
    html_fragment = html_fragment.strip()
    match = _P_WRAP_RE.match(html_fragment)
    if match:
        return match.group(1).strip()
    return html_fragment


def _parse_media_markdown(media_md: str) -> tuple[str, str]:
    match = _MEDIA_PARTS_RE.search(media_md)
    if not match:
        return "", media_md.strip()
    return match.group(1).strip(), match.group(2).strip().split()[0]


def _is_video_path(path: str) -> bool:
    return Path(path).suffix.lower() in _VIDEO_EXTENSIONS


def _build_slide(media_md: str, render_md: Callable[[str], str]) -> str:
    caption, src = _parse_media_markdown(media_md)
    safe_src = html.escape(src, quote=True)
    if _is_video_path(src):
        media_html = (
            f'<video class="xuanxin-gallery-video" controls playsinline preload="metadata" '
            f'src="{safe_src}"></video>'
        )
    else:
        media_html = _normalize_slide_html(render_md(media_md))
    if caption:
        safe_caption = html.escape(caption, quote=True)
        return (
            f'<figure class="xuanxin-gallery-slide" data-caption="{safe_caption}">'
            f"{media_html}</figure>"
        )
    return f'<figure class="xuanxin-gallery-slide">{media_html}</figure>'


def _build_carousel(slides: list[str], *, has_captions: bool, locked: bool = False) -> str:
    total = len(slides)
    track = "".join(slides)
    caption_bar = ""
    if has_captions:
        caption_bar = (
            '  <button type="button" class="xuanxin-gallery-caption" hidden '
            'data-gallery-caption-bar aria-expanded="false"></button>\n'
        )
    classes = ["xuanxin-gallery"]
    if has_captions:
        classes.append("xuanxin-gallery-has-captions")
    if total <= 1:
        classes.append("xuanxin-gallery-single")
    controls = ""
    if total > 1:
        controls = (
            '  <div class="xuanxin-gallery-controls">\n'
            '    <button type="button" class="xuanxin-gallery-btn xuanxin-gallery-prev" '
            'data-gallery-prev aria-label="Previous image">←</button>\n'
            f'    <span class="xuanxin-gallery-indicator" data-gallery-indicator>1 / {total}</span>\n'
            '    <button type="button" class="xuanxin-gallery-btn xuanxin-gallery-next" '
            'data-gallery-next aria-label="Next image">→</button>\n'
            "  </div>\n"
        )
    hidden = " hidden" if locked else ""
    return (
        f'<div class="{" ".join(classes)}" data-gallery{hidden}>\n'
        '  <div class="xuanxin-gallery-viewport">\n'
        f'    <div class="xuanxin-gallery-track">{track}</div>\n'
        "  </div>\n"
        f"{caption_bar}"
        f"{controls}"
        "</div>"
    )


def _wrap_password_gate(carousel_html: str, password: str) -> str:
    pwd_hash = _password_hash(password)
    return (
        f'<div class="xuanxin-gallery-lock" data-gallery-lock '
        f'data-gallery-password-hash="{pwd_hash}">\n'
        '  <form class="xuanxin-gallery-unlock" data-gallery-unlock>\n'
        '    <label class="xuanxin-gallery-unlock-label">Gallery password</label>\n'
        '    <div class="xuanxin-gallery-unlock-row">\n'
        '      <input type="password" class="xuanxin-gallery-unlock-input" '
        'autocomplete="current-password" placeholder="Password" />\n'
        '      <button type="submit" class="xuanxin-gallery-unlock-btn">Unlock</button>\n'
        "    </div>\n"
        '    <p class="xuanxin-gallery-unlock-error" hidden>Wrong password</p>\n'
        "  </form>\n"
        f"{carousel_html}\n"
        "</div>"
    )


def _parse_gallerys_start(line: str) -> str | None:
    """Return gallery password from a GALLERYS line, or empty string if unlocked."""
    match = _START_RE.match(line)
    if not match:
        return None
    return (match.group(1) or "").strip()


def collect_locked_gallery_assets(content: str) -> dict[str, str]:
    """Map local asset paths to gallery passwords."""
    assets: dict[str, str] = {}
    password = ""
    in_gallery = False

    for line in content.splitlines():
        stripped = line.rstrip("\r\n")
        start = _parse_gallerys_start(stripped)
        if start is not None:
            in_gallery = True
            password = start
            continue
        if _END_RE.match(stripped):
            in_gallery = False
            password = ""
            continue
        if not in_gallery or not password:
            continue
        match = _MEDIA_LINE_RE.match(stripped)
        if match:
            _caption, src = _parse_media_markdown(match.group(1))
            if src and not src.startswith(("http://", "https://", "//")):
                assets[src] = password
    return assets


def mark_encrypted_entry_media(page_html: str) -> str:
    """Replace plaintext media URLs in a password-protected diary entry."""
    return _encrypt_media_tags(page_html)


def mark_encrypted_gallery_media(page_html: str) -> str:
    """Replace plaintext media URLs inside locked galleries with encrypted placeholders."""

    def replace_block(block: str) -> str:
        if "data-gallery-password-hash" not in block:
            return block
        return _encrypt_media_tags(block)

    parts = re.split(r'(<div class="xuanxin-gallery-lock"[\s\S]*?</div>\s*</div>)', page_html)
    if len(parts) == 1:
        return page_html
    out: list[str] = []
    for index, part in enumerate(parts):
        out.append(replace_block(part) if index % 2 == 1 else part)
    return "".join(out)


def process_gallery_sections(content: str, render_md: Callable[[str], str]) -> str:
    """Replace GALLERYS/GALLERYE blocks with a horizontal image carousel."""
    lines = content.splitlines(keepends=True)
    out: list[str] = []
    i = 0

    while i < len(lines):
        stripped = lines[i].rstrip("\r\n")
        password = _parse_gallerys_start(stripped)
        if password is None:
            out.append(lines[i])
            i += 1
            continue

        i += 1
        media_lines: list[str] = []
        while i < len(lines):
            line = lines[i]
            stripped = line.rstrip("\r\n")
            if _END_RE.match(stripped):
                i += 1
                break
            match = _MEDIA_LINE_RE.match(stripped)
            if match:
                media_lines.append(match.group(1))
            elif stripped.strip():
                media_lines.append(stripped.lstrip("> ").strip())
            i += 1

        if media_lines:
            slides = [_build_slide(item, render_md) for item in media_lines]
            has_captions = any(_parse_media_markdown(item)[0] for item in media_lines)
            locked = bool(password)
            carousel = _build_carousel(slides, has_captions=has_captions, locked=locked)
            if locked:
                carousel = _wrap_password_gate(carousel, password)
            out.append(carousel + "\n\n")

    return "".join(out)
