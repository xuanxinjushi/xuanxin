"""Build a flat diary site from dated Markdown files."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter

from xuanxin.asset_copy import (
    collect_asset_paths,
    copy_asset_tree,
    copy_assets,
    rewrite_asset_paths,
)
from xuanxin.processor import MarkdownProcessor
from xuanxin.renderer import BlogRenderer

_DATE_STEM_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})$")
_INDEX_PAGE_RE = re.compile(r"^index-(\d+)\.html$")
_DIARY_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
DEFAULT_INDEX_PAGE_SIZE = 20


def normalize_diary_asset_refs(text: str, md_stem: str, input_dir: Path) -> str:
    """Point image refs at ``{md_stem}/`` when the filename exists in that folder."""
    asset_dir = input_dir / md_stem
    if not asset_dir.is_dir():
        return text

    def repl(match: re.Match[str]) -> str:
        alt, path = match.group(1), _normalize_asset_ref(match.group(2))
        filename = Path(path).name
        if (asset_dir / filename).is_file():
            return f"![{alt}]({md_stem}/{filename})"
        return match.group(0)

    return _DIARY_IMAGE_RE.sub(repl, text)


def _normalize_asset_ref(path: str) -> str:
    return path.strip().split()[0]


def date_from_stem(stem: str) -> datetime | None:
    """Parse YYYYMMDD filename stems into a datetime."""
    match = _DATE_STEM_RE.match(stem)
    if not match:
        return None
    year, month, day = (int(match.group(i)) for i in range(1, 4))
    try:
        return datetime(year, month, day)
    except ValueError:
        return None


def normalize_home_url(url: str) -> str:
    """Ensure external home links include a scheme."""
    url = url.strip()
    if not url:
        return url
    if "://" not in url:
        return f"https://{url}"
    return url


def diary_index_filename(page: int) -> str:
    """Return the HTML filename for a diary index page (1-based)."""
    if page <= 1:
        return "index.html"
    return f"index-{page}.html"


def index_page_count(entry_count: int, page_size: int) -> int:
    """Return how many index pages are needed."""
    if entry_count == 0:
        return 1
    return math.ceil(entry_count / page_size)


@dataclass
class DiaryBuilder:
    """Scan dated Markdown files and emit a flat HTML diary site."""

    input_dir: Path
    output_dir: Path
    home_url: str = ""
    gtag_path: Path | None = None
    site_title: str = "Diary"
    theme: str = "default"
    custom_css: Path | None = None
    mathjax: bool = True
    index_page_size: int = DEFAULT_INDEX_PAGE_SIZE
    processor: MarkdownProcessor = field(default_factory=MarkdownProcessor)

    def build(self) -> dict[str, Any]:
        self.input_dir = Path(self.input_dir).resolve()
        self.output_dir = Path(self.output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        gtag_path = Path(self.gtag_path).resolve() if self.gtag_path else None
        gtag_snippet = gtag_path.read_text(encoding="utf-8") if gtag_path and gtag_path.is_file() else ""
        home_url = normalize_home_url(self.home_url)

        renderer = BlogRenderer(
            site_title=self.site_title,
            theme=self.theme,
            custom_css=self.custom_css,
            mathjax=self.mathjax,
        )
        renderer.copy_static_assets(self.output_dir, self.custom_css)

        md_files = sorted(
            p for p in self.input_dir.glob("*.md") if p.is_file() and not p.name.startswith(".")
        )

        entries: list[dict[str, Any]] = []
        built: list[str] = []
        copied_assets: list[str] = []

        for md_path in md_files:
            raw_text = md_path.read_text(encoding="utf-8")
            raw_text = normalize_diary_asset_refs(raw_text, md_path.stem, self.input_dir)
            result = self._process_diary_file(md_path, raw_text)
            if not result:
                continue

            asset_paths = collect_asset_paths(raw_text, result["content"])
            path_rewrites: dict[str, str] = {}
            copied, asset_rewrites = copy_assets(
                asset_paths, source_root=self.input_dir, output_root=self.output_dir
            )
            copied_assets.extend(copied)
            path_rewrites.update(asset_rewrites)
            asset_dir = self.input_dir / md_path.stem
            if asset_dir.is_dir():
                tree_copied, tree_rewrites = copy_asset_tree(
                    asset_dir, source_root=self.input_dir, output_root=self.output_dir
                )
                copied_assets.extend(tree_copied)
                path_rewrites.update(tree_rewrites)

            html_name = f"{md_path.stem}.html"
            out_file = self.output_dir / html_name
            content = rewrite_asset_paths(result["content"], path_rewrites)
            html = renderer.render_diary_post(
                {**result, "content": content},
                home_url=home_url,
                gtag_snippet=gtag_snippet,
                index_href="index.html",
            )
            out_file.write_text(html, encoding="utf-8")
            built.append(str(out_file))

            entries.append(
                {
                    "title": result["metadata"]["title"],
                    "href": html_name,
                    "date": result["metadata"]["date"],
                    "source": str(md_path),
                }
            )

        entries.sort(key=lambda item: item["date"], reverse=True)

        page_size = max(1, self.index_page_size)
        total_pages = index_page_count(len(entries), page_size)
        for page in range(1, total_pages + 1):
            start = (page - 1) * page_size
            page_entries = entries[start : start + page_size]
            index_name = diary_index_filename(page)
            index_path = self.output_dir / index_name
            prev_href = diary_index_filename(page - 1) if page > 1 else None
            next_href = diary_index_filename(page + 1) if page < total_pages else None
            index_html = renderer.render_diary_index(
                page_entries,
                home_url=home_url,
                gtag_snippet=gtag_snippet,
                page=page,
                total_pages=total_pages,
                total_entries=len(entries),
                list_start=(page - 1) * page_size + 1,
                prev_href=prev_href,
                next_href=next_href,
            )
            index_path.write_text(index_html, encoding="utf-8")
            built.append(str(index_path))

        self._remove_stale_index_pages(total_pages)

        return {
            "built": built,
            "copied_assets": copied_assets,
            "count": len(entries),
            "index_pages": total_pages,
            "output_dir": str(self.output_dir),
        }

    def _remove_stale_index_pages(self, total_pages: int) -> None:
        for path in self.output_dir.glob("index-*.html"):
            match = _INDEX_PAGE_RE.match(path.name)
            if match and int(match.group(1)) > total_pages:
                path.unlink()

    def _process_diary_file(self, md_path: Path, text: str | None = None) -> dict[str, Any] | None:
        text = text if text is not None else md_path.read_text(encoding="utf-8")
        post = frontmatter.loads(text)
        result = self.processor.process_string(text, source_file=str(md_path))
        if not result:
            return None

        meta = result["metadata"]
        file_date = date_from_stem(md_path.stem)
        if file_date and "date" not in post.metadata:
            meta["date"] = file_date
        if meta["title"] == "Untitled" and file_date:
            meta["title"] = file_date.strftime("%B %d, %Y")
        return result
