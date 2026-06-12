"""Autolink bare http(s) URLs in Markdown and HTML."""

from __future__ import annotations

import re

_FENCED_CODE_RE = re.compile(r"```[\s\S]*?```")
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_DISPLAY_MATH_RE = re.compile(r"\$\$[\s\S]*?\$\$")
_INLINE_MATH_RE = re.compile(r"\$[^$\n]+?\$")
_URL_RE = re.compile(
    r"(?<!\()(?<!\[)(?<!<)(https?://[^\s<>\[\]`]+(?:\([^\s<>\[\]`]*\)[^\s<>\[\]`]*)*)"
)
_HTML_TAG_RE = re.compile(r"(<[^>]+>)")


def _trim_trailing_punct(url: str) -> tuple[str, str]:
    extra = ""
    while url:
        ch = url[-1]
        if ch in ".,;:!?":
            extra = ch + extra
            url = url[:-1]
            continue
        if ch == ")" and url.count("(") < url.count(")"):
            extra = ch + extra
            url = url[:-1]
            continue
        break
    return url, extra


def _autolink_segment(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        url, extra = _trim_trailing_punct(match.group(1))
        if not url:
            return match.group(0)
        return f"<{url}>{extra}"

    return _URL_RE.sub(repl, text)


def autolink_markdown_urls(content: str) -> str:
    """Autolink bare URLs outside code blocks and LaTeX (Markdown stage)."""
    protected: list[str] = []

    def protect(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"\x00AUTOLINK{len(protected) - 1}\x00"

    masked = _FENCED_CODE_RE.sub(protect, content)
    masked = _INLINE_CODE_RE.sub(protect, masked)
    masked = _DISPLAY_MATH_RE.sub(protect, masked)
    masked = _INLINE_MATH_RE.sub(protect, masked)
    linked = _autolink_segment(masked)
    for index, original in enumerate(protected):
        linked = linked.replace(f"\x00AUTOLINK{index}\x00", original)
    return linked


def autolink_html(html: str) -> str:
    """Autolink bare URLs in rendered HTML, skipping anchors and code blocks."""
    parts = _HTML_TAG_RE.split(html)
    skip_depth = 0
    out: list[str] = []

    for part in parts:
        if not part:
            continue
        if part.startswith("<"):
            lower = part.lower()
            if lower.startswith("<a ") or lower == "<a>":
                skip_depth += 1
            elif lower.startswith("</a"):
                skip_depth = max(0, skip_depth - 1)
            elif lower.startswith("<pre") or lower.startswith("<code"):
                skip_depth += 1
            elif lower.startswith("</pre") or lower.startswith("</code"):
                skip_depth = max(0, skip_depth - 1)
            out.append(part)
            continue

        if skip_depth:
            out.append(part)
        else:
            out.append(_autolink_html_text(part))

    return "".join(out)


_MATH_HTML_RE = re.compile(r"(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$)")


def _autolink_html_text(text: str) -> str:
    protected: list[str] = []

    def protect(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"\x00MATH{len(protected) - 1}\x00"

    masked = _MATH_HTML_RE.sub(protect, text)
    linked = _autolink_html_segment(masked)
    for index, original in enumerate(protected):
        linked = linked.replace(f"\x00MATH{index}\x00", original)
    return linked


def _autolink_html_segment(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        url, extra = _trim_trailing_punct(match.group(1))
        if not url:
            return match.group(0)
        return f'<a href="{url}">{url}</a>{extra}'

    return _URL_RE.sub(repl, text)
