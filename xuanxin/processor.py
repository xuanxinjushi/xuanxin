"""Markdown → HTML processor extracted from MockSphere content_import."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter
import markdown

from xuanxin.extensions import ImageClassesExtension, VideoEmbedExtension
from xuanxin.latex import protect_latex, restore_latex


def _default_extensions() -> list[Any]:
    return [
        "markdown.extensions.extra",
        "markdown.extensions.codehilite",
        "markdown.extensions.toc",
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        "markdown.extensions.attr_list",
        "markdown.extensions.nl2br",
        ImageClassesExtension(),
        VideoEmbedExtension(),
    ]


class MarkdownProcessor:
    """Parse YAML frontmatter + Markdown body and return structured HTML."""

    def __init__(self, *, codehilite_css_class: str = "highlight"):
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
        metadata = self._parse_metadata(post.metadata)

        protected, placeholders = protect_latex(post.content)
        html = self._md.convert(protected)
        html = restore_latex(html, placeholders)
        self._md.reset()

        return {
            "metadata": metadata,
            "content": html,
            "raw_content": post.content,
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


def process_file(file_path: Path | str) -> dict[str, Any] | None:
    return MarkdownProcessor().process_file(file_path)


def process_string(content: str, *, source_file: str | None = None) -> dict[str, Any]:
    return MarkdownProcessor().process_string(content, source_file=source_file)
