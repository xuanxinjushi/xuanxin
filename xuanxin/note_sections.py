"""NOTES/NOTEE, IMPORS/IMPORE, and WARNS/WARNE block sections (bubble-compatible)."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

_SECTION_SPECS = (
    ("NOTES:", "NOTEE", "xuanxin-notesection"),
    ("IMPORS:", "IMPORE", "xuanxin-importantsection"),
    ("WARNS:", "WARNE", "xuanxin-warnsection"),
)

_BLOCKQUOTE_LINE = re.compile(r"^>\s?(.*)$")


@dataclass(frozen=True)
class _SectionSpec:
    start: str
    end: str
    css_class: str
    start_re: re.Pattern[str]
    end_re: re.Pattern[str]


def _build_specs() -> tuple[_SectionSpec, ...]:
    specs: list[_SectionSpec] = []
    for start, end, css_class in _SECTION_SPECS:
        specs.append(
            _SectionSpec(
                start=start,
                end=end,
                css_class=css_class,
                start_re=re.compile(rf"^>\s*{re.escape(start)}\s*(.*)$"),
                end_re=re.compile(rf"^>\s*{re.escape(end)}\s*$"),
            )
        )
    return tuple(specs)


_SPECS = _build_specs()


def _match_start(line: str) -> tuple[_SectionSpec, str] | None:
    for spec in _SPECS:
        match = spec.start_re.match(line)
        if match:
            return spec, match.group(1)
    return None


def process_note_sections(content: str, render_md: Callable[[str], str]) -> str:
    """Replace bubble-style note/important/warning sections with styled HTML asides."""
    lines = content.splitlines(keepends=True)
    out: list[str] = []
    i = 0

    while i < len(lines):
        stripped = lines[i].rstrip("\r\n")
        start = _match_start(stripped)
        if not start:
            out.append(lines[i])
            i += 1
            continue

        spec, head = start
        paragraphs: list[str] = []
        current: list[str] = []

        def flush() -> None:
            if current:
                paragraphs.append("\n".join(current))
                current.clear()

        if head.strip():
            current.append(head.strip())
        i += 1

        while i < len(lines):
            line = lines[i]
            stripped = line.rstrip("\r\n")
            if spec.end_re.match(stripped):
                flush()
                i += 1
                break
            if not stripped.strip():
                flush()
                i += 1
                continue

            bq = _BLOCKQUOTE_LINE.match(stripped)
            if bq:
                text = bq.group(1)
                if text.strip():
                    current.append(text)
            else:
                current.append(stripped)
            i += 1

        inner_md = "\n\n".join(paragraphs).strip()
        if inner_md:
            inner_html = render_md(inner_md).strip()
            out.append(f'<aside class="{spec.css_class}">\n{inner_html}\n</aside>\n\n')

    return "".join(out)
