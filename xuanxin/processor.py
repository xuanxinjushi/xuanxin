"""Markdown → HTML processor extracted from MockSphere content_import."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter
import markdown

from xuanxin.extensions import (
    BackslashBlankLineExtension,
    ImageAttributesExtension,
    ImageClassesExtension,
    LatexFencedBlockExtension,
    LatexPageBreakExtension,
    TpImageExtension,
    VideoEmbedExtension,
)
from xuanxin.footnotes import reorder_footnotes_before_chapter_poster
from xuanxin.gallery_sections import process_gallery_sections
from xuanxin.includes import find_peanut_config, load_config, process_includes
from xuanxin.latex import protect_latex, restore_latex
from xuanxin.note_sections import process_note_sections
from xuanxin.section_nav import inject_section_nav

# First markdown H1, optional Pandoc attrs e.g. `# Chapter 1: 山 {-}`
_FIRST_H1_LINE_RE = re.compile(r"^#\s+(.+?)(?:\s+\{[^}]*\})?\s*$")


def _extract_first_h1_title(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = _FIRST_H1_LINE_RE.match(stripped)
        if match:
            return match.group(1).strip()
    return None


def _strip_first_h1(content: str) -> str:
    lines = content.splitlines(keepends=True)
    out: list[str] = []
    removed = False
    for line in lines:
        if not removed and _FIRST_H1_LINE_RE.match(line.strip()):
            removed = True
            continue
        out.append(line)
    return "".join(out).lstrip("\n")


def _default_extensions() -> list[Any]:
    return [
        "markdown.extensions.extra",
        "markdown.extensions.codehilite",
        "markdown.extensions.toc",
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        "markdown.extensions.attr_list",
        "markdown.extensions.nl2br",
        LatexFencedBlockExtension(),
        LatexPageBreakExtension(),
        TpImageExtension(),
        BackslashBlankLineExtension(),
        ImageClassesExtension(),
        ImageAttributesExtension(),
        VideoEmbedExtension(),
    ]


class MarkdownProcessor:
    """Parse YAML frontmatter + Markdown body and return structured HTML."""

    def __init__(
        self,
        *,
        codehilite_css_class: str = "highlight",
        include_config: Path | str | None = None,
    ):
        self._include_config = (
            Path(include_config).resolve() if include_config else None
        )
        self._md = markdown.Markdown(
            extensions=_default_extensions(),
            extension_configs={
                "markdown.extensions.codehilite": {
                    "css_class": codehilite_css_class,
                    "guess_lang": True,
                },
                "markdown.extensions.toc": {"permalink": True, "toc_depth": 3},
            },
        )

    def process_file(self, file_path: Path | str) -> dict[str, Any] | None:
        path = Path(file_path)
        try:
            text = path.read_text(encoding="utf-8")
            return self.process_string(text, source_file=str(path))
        except OSError as exc:
            raise RuntimeError(f"Cannot read {path}: {exc}") from exc

    def process_string(
        self, content: str, *, source_file: str | None = None
    ) -> dict[str, Any]:
        post = frontmatter.loads(content)
        metadata = dict(post.metadata)
        body = post.content
        body = self._expand_includes(body, source_file=source_file)

        if not metadata.get("title"):
            extracted = _extract_first_h1_title(body)
            if extracted:
                metadata["title"] = extracted
                body = _strip_first_h1(body)

        parsed = self._parse_metadata(metadata)

        body = process_gallery_sections(body, self._render_markdown_fragment)
        body = process_note_sections(body, self._render_markdown_fragment)
        protected, placeholders = protect_latex(body)
        html = self._md.convert(protected)
        html = restore_latex(html, placeholders)
        html = reorder_footnotes_before_chapter_poster(html)
        html = inject_section_nav(html)
        self._md.reset()

        return {
            "metadata": parsed,
            "content": html,
            "raw_content": body,
            "source_file": source_file,
        }

    def _parse_metadata(self, raw: dict[str, Any]) -> dict[str, Any]:
        title = raw.get("title", "Untitled")
        return {
            "title": title,
            "slug": self._slug(raw.get("slug") or title),
            "date": self._parse_date(raw.get("date")),
            "tags": self._parse_tags(raw.get("tags", [])),
            "author": raw.get("author", ""),
            "draft": bool(raw.get("draft", False)),
            "description": raw.get("description", ""),
            "categories": raw.get("categories", []),
            "featured_image_url": raw.get("featured_image_url", ""),
            "theme": raw.get("theme", ""),
            "math": bool(raw.get("math", True)),
            "password": str(raw.get("password", "")).strip().strip('"').strip("'"),
        }

    @staticmethod
    def _slug(text: str) -> str:
        slug = re.sub(r"[^\w\s-]", "", str(text).lower())
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug.strip("-") or "untitled"

    @staticmethod
    def _parse_date(value: Any) -> datetime:
        if not value:
            return datetime.now()
        if isinstance(value, datetime):
            return value
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        return datetime.now()

    @staticmethod
    def _parse_tags(tags: Any) -> list[str]:
        if isinstance(tags, str):
            return [t.strip() for t in tags.split(",") if t.strip()]
        if isinstance(tags, list):
            return [str(t).strip() for t in tags]
        return []


    def _render_markdown_fragment(self, md_text: str) -> str:
        protected, placeholders = protect_latex(md_text)
        html = self._md.convert(protected)
        html = restore_latex(html, placeholders)
        self._md.reset()
        return html

    def _expand_includes(self, body: str, *, source_file: str | None) -> str:
        if not source_file or "<!-- include:" not in body:
            return body
        base_dir = Path(source_file).parent
        config_path = self._include_config or find_peanut_config(base_dir)
        config = load_config(config_path)
        return process_includes(body, base_dir, config)


def process_file(file_path: Path | str) -> dict[str, Any] | None:
    return MarkdownProcessor().process_file(file_path)


def process_string(content: str, *, source_file: str | None = None) -> dict[str, Any]:
    return MarkdownProcessor().process_string(content, source_file=source_file)
