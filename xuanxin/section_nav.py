"""Turn chapter section subtitles (*A、B、C*) into in-page navigation buttons."""

from __future__ import annotations

import re

H2_RE = re.compile(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', re.DOTALL | re.IGNORECASE)
HEADERLINK_RE = re.compile(r'<a class="headerlink"[^>]*>.*?</a>', re.DOTALL | re.IGNORECASE)
SUBTITLE_EM_RE = re.compile(r"<p><em>([^<]+)</em></p>", re.IGNORECASE)

SECTION_SEPARATORS = (" · ", "、", ", ")


def _split_section_names(text: str) -> list[str]:
    for sep in SECTION_SEPARATORS:
        if sep in text:
            return [part.strip() for part in text.split(sep) if part.strip()]
    return []


def _h2_text(inner_html: str) -> str:
    return HEADERLINK_RE.sub("", inner_html).strip()


def _collect_h2_headings(html: str) -> list[tuple[str, str]]:
    return [(match.group(1), _h2_text(match.group(2))) for match in H2_RE.finditer(html)]


def inject_section_nav(html: str) -> str:
    """Replace the italic section list under the chapter title with nav buttons."""
    headings = _collect_h2_headings(html)
    if len(headings) < 2:
        return html

    match = SUBTITLE_EM_RE.search(html)
    if not match:
        return html

    first_h2 = html.lower().find("<h2")
    if first_h2 != -1 and match.start() > first_h2:
        return html

    names = _split_section_names(match.group(1))
    if len(names) != len(headings):
        return html

    buttons = []
    for label, (section_id, _heading) in zip(names, headings):
        buttons.append(
            f'<a class="xuanxin-section-nav-btn" href="#{section_id}">{label}</a>'
        )

    nav = (
        '<nav class="xuanxin-section-nav" aria-label="Sections">'
        + "".join(buttons)
        + "</nav>"
    )
    return html[: match.start()] + nav + html[match.end() :]
