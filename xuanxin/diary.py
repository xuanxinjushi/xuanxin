"""Build a flat diary site from dated Markdown files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter

from xuanxin.processor import MarkdownProcessor
from xuanxin.renderer import BlogRenderer

_DATE_STEM_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})$")


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


def is_stale(output: Path, *sources: Path) -> bool:
    """Return True when output is missing or older than any source file."""
    if not output.exists():
        return True
    out_mtime = output.stat().st_mtime
    for src in sources:
        if src.exists() and src.stat().st_mtime > out_mtime:
            return True
    return False


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
        skipped: list[str] = []
        cache_sources = [p for p in (gtag_path,) if p and p.is_file()]

        for md_path in md_files:
            result = self._process_diary_file(md_path)
            if not result:
                skipped.append(str(md_path))
                continue

            html_name = f"{md_path.stem}.html"
            out_file = self.output_dir / html_name
            entry_sources = [md_path, *cache_sources]

            if is_stale(out_file, *entry_sources):
                html = renderer.render_diary_post(
                    result,
                    home_url=home_url,
                    gtag_snippet=gtag_snippet,
                    index_href="index.html",
                )
                out_file.write_text(html, encoding="utf-8")
                built.append(str(out_file))
            else:
                skipped.append(str(out_file))

            entries.append(
                {
                    "title": result["metadata"]["title"],
                    "href": html_name,
                    "date": result["metadata"]["date"],
                    "source": str(md_path),
                }
            )

        entries.sort(key=lambda item: item["date"], reverse=True)

        index_path = self.output_dir / "index.html"
        index_sources = [*md_files, *cache_sources]
        if is_stale(index_path, *index_sources) or built:
            index_html = renderer.render_diary_index(
                entries,
                home_url=home_url,
                gtag_snippet=gtag_snippet,
            )
            index_path.write_text(index_html, encoding="utf-8")
            if str(index_path) not in built:
                built.insert(0, str(index_path))
        else:
            skipped.append(str(index_path))

        return {
            "built": built,
            "skipped": skipped,
            "count": len(entries),
            "output_dir": str(self.output_dir),
        }

    def _process_diary_file(self, md_path: Path) -> dict[str, Any] | None:
        text = md_path.read_text(encoding="utf-8")
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
