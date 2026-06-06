"""Build static HTML site from Markdown blog files."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from xuanxin.processor import MarkdownProcessor
from xuanxin.renderer import BlogRenderer


@dataclass
class BlogBuilder:
    """Scan a content directory and emit a static HTML blog."""

    content_dir: Path
    output_dir: Path
    site_title: str = "Blog"
    site_description: str = ""
    base_url: str = ""
    theme: str = "default"
    custom_css: Path | None = None
    pattern: str = "**/*.md"
    include_drafts: bool = False
    mathjax: bool = True
    processor: MarkdownProcessor = field(default_factory=MarkdownProcessor)

    def build(self) -> dict[str, Any]:
        self.content_dir = Path(self.content_dir)
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        posts_dir = self.output_dir / "posts"
        posts_dir.mkdir(exist_ok=True)

        renderer = BlogRenderer(
            site_title=self.site_title,
            site_description=self.site_description,
            base_url=self.base_url,
            theme=self.theme,
            custom_css=self.custom_css,
            mathjax=self.mathjax,
        )
        renderer.copy_static_assets(self.output_dir, self.custom_css)

        posts: list[dict[str, Any]] = []
        built: list[str] = []
        skipped: list[str] = []

        for md_path in sorted(self.content_dir.glob(self.pattern)):
            if md_path.name.startswith("."):
                continue
            result = self.processor.process_file(md_path)
            if not result:
                skipped.append(str(md_path))
                continue

            meta = result["metadata"]
            if meta.get("draft") and not self.include_drafts:
                skipped.append(str(md_path))
                continue

            posts.append(result)
            out_file = posts_dir / f"{meta['slug']}.html"
            out_file.write_text(renderer.render_post(result), encoding="utf-8")
            built.append(str(out_file))

        index_html = renderer.render_index(posts)
        (self.output_dir / "index.html").write_text(index_html, encoding="utf-8")

        manifest = {
            "site_title": self.site_title,
            "posts": [
                {
                    "title": p["metadata"]["title"],
                    "slug": p["metadata"]["slug"],
                    "date": p["metadata"]["date"].isoformat(),
                    "source": p.get("source_file"),
                }
                for p in posts
            ],
        }
        (self.output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

        return {"built": built, "skipped": skipped, "count": len(built)}


def render_file(
    md_path: Path | str,
    *,
    output_dir: Path | None = None,
    site_title: str = "Blog",
    theme: str = "default",
    custom_css: Path | None = None,
    mathjax: bool = True,
    processor: MarkdownProcessor | None = None,
) -> Path:
    """Render one Markdown file to {stem}.html in the current directory."""
    md_path = Path(md_path).resolve()
    if not md_path.exists():
        raise FileNotFoundError(md_path)

    out_dir = Path(output_dir or Path.cwd()).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{md_path.stem}.html"

    proc = processor or MarkdownProcessor()
    result = proc.process_file(md_path)
    if not result:
        raise RuntimeError(f"Failed to process {md_path}")

    renderer = BlogRenderer(
        site_title=site_title,
        base_url="",
        theme=theme,
        custom_css=custom_css,
        mathjax=mathjax,
    )
    renderer.copy_static_assets(out_dir, custom_css)
    out_file.write_text(renderer.render_post(result), encoding="utf-8")
    return out_file
