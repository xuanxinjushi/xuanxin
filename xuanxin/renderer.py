"""Render blog pages from processed posts using Jinja2 templates."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from xuanxin.paginate import paginate_content


PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE_DIR = PACKAGE_DIR / "templates"
DEFAULT_THEME_DIR = PACKAGE_DIR / "static" / "themes"


class BlogRenderer:
    """Wrap Jinja2 templates for index and post pages."""

    def __init__(
        self,
        *,
        site_title: str = "Blog",
        site_description: str = "",
        base_url: str = "",
        theme: str = "default",
        custom_css: Path | None = None,
        template_dir: Path | None = None,
        mathjax: bool = True,
    ):
        self.site_title = site_title
        self.site_description = site_description
        self.base_url = base_url.rstrip("/")
        self.theme = theme
        self.custom_css = custom_css
        self.mathjax = mathjax
        tpl_dir = template_dir or DEFAULT_TEMPLATE_DIR
        self.env = Environment(
            loader=FileSystemLoader(str(tpl_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _assets_prefix(self) -> str:
        return f"{self.base_url}/" if self.base_url else ""

    def render_post(
        self,
        post: dict[str, Any],
        *,
        book_mode: bool = False,
        prev_href: str | None = None,
        prev_title: str | None = None,
        next_href: str | None = None,
        next_title: str | None = None,
        prev_chapter_pages: int = 0,
    ) -> str:
        meta = post["metadata"]
        use_math = meta.get("math", self.mathjax)
        content, page_count = paginate_content(post["content"])
        paginated = page_count > 1
        template = self.env.get_template("post.html")
        return template.render(
            site_title=self.site_title,
            site_theme=self.theme,
            base_url=self.base_url,
            assets_prefix=self._assets_prefix(),
            title=meta["title"],
            slug=meta["slug"],
            date=meta["date"],
            author=meta["author"],
            tags=meta["tags"],
            description=meta["description"],
            featured_image_url=meta.get("featured_image_url", ""),
            content=content,
            theme=self._resolve_theme(meta),
            custom_css=self._custom_css_href(),
            mathjax=use_math,
            standalone=not self.base_url,
            book_mode=book_mode,
            prev_href=prev_href,
            prev_title=prev_title,
            next_href=next_href,
            next_title=next_title,
            paginated=paginated,
            page_count=page_count,
            prev_chapter_pages=prev_chapter_pages,
        )

    def render_book_index(
        self,
        chapters: list[dict[str, Any]],
        *,
        site_title: str | None = None,
    ) -> str:
        template = self.env.get_template("book_index.html")
        return template.render(
            site_title=site_title if site_title is not None else self.site_title,
            site_description=self.site_description,
            assets_prefix=self._assets_prefix(),
            chapters=chapters,
            theme=self.theme,
            custom_css=self._custom_css_href(),
        )

    def render_index(self, posts: list[dict[str, Any]]) -> str:
        template = self.env.get_template("index.html")
        items = []
        for post in posts:
            meta = post["metadata"]
            if meta.get("draft"):
                continue
            items.append(
                {
                    "title": meta["title"],
                    "slug": meta["slug"],
                    "date": meta["date"],
                    "author": meta["author"],
                    "tags": meta["tags"],
                    "description": meta["description"],
                    "url": f"{self.base_url}/posts/{meta['slug']}.html",
                }
            )
        items.sort(key=lambda p: p["date"], reverse=True)
        return template.render(
            site_title=self.site_title,
            site_description=self.site_description,
            base_url=self.base_url,
            assets_prefix=self._assets_prefix(),
            posts=items,
            theme=self.theme,
            custom_css=self._custom_css_href(),
        )

    def _resolve_theme(self, meta: dict[str, Any]) -> str:
        return meta.get("theme") or self.theme

    def _custom_css_href(self) -> str | None:
        if self.custom_css:
            return f"{self._assets_prefix()}assets/custom.css"
        return None

    def copy_static_assets(self, output_dir: Path, custom_css: Path | None = None) -> None:
        """Copy theme CSS and optional custom CSS into output/assets/."""
        assets = output_dir / "assets"
        assets.mkdir(parents=True, exist_ok=True)

        theme_vars = DEFAULT_THEME_DIR / f"{self.theme}.css"
        if not theme_vars.exists():
            theme_vars = DEFAULT_THEME_DIR / "default.css"

        base_css = DEFAULT_THEME_DIR / "_base.css"
        parts = []
        if theme_vars.exists():
            parts.append(theme_vars.read_text(encoding="utf-8"))
        if base_css.exists():
            parts.append(base_css.read_text(encoding="utf-8"))
        (assets / "theme.css").write_text("\n".join(parts), encoding="utf-8")

        # Per-post theme overrides (frontmatter `theme:` field)
        themes_sub = assets / "themes"
        themes_sub.mkdir(exist_ok=True)
        for css in DEFAULT_THEME_DIR.glob("*.css"):
            if css.name.startswith("_"):
                continue
            shutil.copy2(css, themes_sub / css.name)

        if custom_css and custom_css.exists():
            shutil.copy2(custom_css, assets / "custom.css")

        page_reader_js = PACKAGE_DIR / "static" / "page-reader.js"
        if page_reader_js.exists():
            shutil.copy2(page_reader_js, assets / "page-reader.js")
