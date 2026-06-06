"""Split HTML at page-break markers into paginated reader pages."""

from __future__ import annotations

import re

PAGE_BREAK_RE = re.compile(
    r'<div class="xuanxin-pagebreak"[^>]*></div>',
    re.IGNORECASE,
)


def count_pages(html: str) -> int:
    """Return how many reader pages ``html`` would split into."""
    if "xuanxin-pagebreak" not in html:
        return 1
    parts = PAGE_BREAK_RE.split(html)
    pages = [part for part in parts if part.strip()]
    return max(len(pages), 1)


def paginate_content(html: str) -> tuple[str, int]:
    """Wrap HTML fragments separated by page breaks in a paginated reader."""
    if "xuanxin-paginated-reader" in html:
        match = re.search(r'data-page-count="(\d+)"', html)
        return html, int(match.group(1)) if match else 1

    if "xuanxin-pagebreak" not in html:
        return html, 1

    parts = PAGE_BREAK_RE.split(html)
    pages = [part.strip() for part in parts if part.strip()]
    if len(pages) <= 1:
        return html, 1

    wrapped: list[str] = []
    for index, page_html in enumerate(pages, start=1):
        hidden = " hidden" if index > 1 else ""
        wrapped.append(
            f'<div class="xuanxin-page" data-page="{index}"{hidden}>{page_html}</div>'
        )

    reader = (
        f'<div class="xuanxin-paginated-reader" data-page-count="{len(pages)}">'
        + "".join(wrapped)
        + "</div>"
    )
    return reader, len(pages)
