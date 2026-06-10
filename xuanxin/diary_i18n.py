"""Diary filename language parsing and navigation helpers."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

_DIARY_STEM_RE = re.compile(r"^(\d{8})(?:_([a-z]{2}))?$")

LANG_LABELS = {
    "en": "English",
    "zh": "中文",
}


def parse_diary_stem(stem: str) -> tuple[str, str]:
    """Return ``(base_date, lang)`` for diary markdown stems."""
    match = _DIARY_STEM_RE.match(stem)
    if not match:
        return stem, "en"
    return match.group(1), match.group(2) or "en"


def lang_label(code: str) -> str:
    return LANG_LABELS.get(code, code.upper())


def group_entries_by_date(
    processed: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    """Collapse multilingual variants into one index row per calendar day."""
    by_date: dict[str, dict[str, Any]] = {}
    alternates: dict[str, dict[str, str]] = {}

    for item in processed:
        base_date, lang = parse_diary_stem(item["stem"])
        alternates.setdefault(base_date, {})[lang] = item["html_name"]

        current = by_date.get(base_date)
        if current is None or (current["lang"] != "en" and lang == "en"):
            by_date[base_date] = {
                **item,
                "base_date": base_date,
                "lang": lang,
                "href": item["html_name"],
            }

    index_entries = sorted(by_date.values(), key=lambda row: row["date"], reverse=True)
    return index_entries, alternates


def _pick_href(langs: dict[str, str], lang: str) -> str | None:
    if lang in langs:
        return langs[lang]
    if "en" in langs:
        return langs["en"]
    return next(iter(langs.values()), None)


def build_day_navigation(
    processed: list[dict[str, Any]],
) -> dict[str, dict[str, str | None]]:
    """Return prev/next href map keyed by output HTML filename."""
    by_base: dict[str, dict[str, str]] = {}
    for item in processed:
        base_date, lang = parse_diary_stem(item["stem"])
        by_base.setdefault(base_date, {})[lang] = item["html_name"]

    ordered = sorted(by_base.items(), key=lambda pair: datetime.strptime(pair[0], "%Y%m%d"))
    nav: dict[str, dict[str, str | None]] = {}

    for index, (_base_date, langs) in enumerate(ordered):
        prev_langs = ordered[index - 1][1] if index > 0 else {}
        next_langs = ordered[index + 1][1] if index + 1 < len(ordered) else {}
        for lang, href in langs.items():
            prev_href = _pick_href(prev_langs, lang) if prev_langs else None
            next_href = _pick_href(next_langs, lang) if next_langs else None
            nav[href] = {"prev_href": prev_href, "next_href": next_href}

    return nav


def build_alternates_meta(
    processed: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, str]]]:
    """Map calendar days to per-language href/title metadata for the index."""
    meta: dict[str, dict[str, dict[str, str]]] = {}
    for item in processed:
        base_date, lang = parse_diary_stem(item["stem"])
        meta.setdefault(base_date, {})[lang] = {
            "href": item["html_name"],
            "title": item["title"],
        }
    return meta


def index_language_options(alternates: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    """Return sorted language choices for the diary index header."""
    codes = sorted(
        {code for langs in alternates.values() for code in langs},
        key=lambda value: (value != "en", value),
    )
    return [{"code": code, "label": lang_label(code)} for code in codes]


def language_links_for(
    html_name: str,
    alternates: dict[str, dict[str, str]],
    stem: str,
) -> list[dict[str, str]]:
    """Build language switch links for one diary page."""
    base_date, current_lang = parse_diary_stem(stem)
    langs = alternates.get(base_date, {})
    links: list[dict[str, str]] = []
    for code in sorted(langs, key=lambda value: (value != "en", value)):
        href = langs[code]
        links.append(
            {
                "code": code,
                "label": lang_label(code),
                "href": href,
                "current": href == html_name,
            }
        )
    return links
