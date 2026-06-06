"""Discover and render autobiography / bubble-style book chapters to HTML."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xuanxin.includes import find_peanut_config
from xuanxin.paginate import count_pages
from xuanxin.processor import MarkdownProcessor
from xuanxin.renderer import BlogRenderer

# Bubble merge order: preface → chapters 1–12 → appendix (chapterx)
LANG_SUFFIX = {
    "en": "",
    "zh": "_zh",
    "cn": "_zh",
    "tc": "_tc",
    "jp": "_jp",
    "sp": "_sp",
}


@dataclass
class BookChapter:
    """One rendered unit in reading order."""

    md_path: Path
    html_name: str
    title: str
    order: int


def is_book_repo_root(path: Path) -> bool:
    root = path.resolve()
    if next(root.glob("chapter1-*"), None) is not None:
        return True
    chapterx = root / "chapterx"
    return chapterx.is_dir() and any(chapterx.glob("*.md"))


def discover_book_repo_root(start: Path | None = None) -> Path:
    seen: set[Path] = set()
    cur = (start or Path.cwd()).resolve()
    while cur not in seen:
        seen.add(cur)
        if is_book_repo_root(cur):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise FileNotFoundError(
        "Cannot find book repository root (expected chapter1-*/ or chapterx/). "
        "Run from the book repo or pass --root."
    )


def collect_book_markdown(root: Path, lang: str = "en") -> list[Path]:
    """Return markdown files in reading order (preface, ch.1–12, appendix)."""
    root = root.resolve()
    suffix = LANG_SUFFIX.get(lang, lang if lang.startswith("_") else "")
    if lang not in LANG_SUFFIX and not suffix.startswith("_"):
        suffix = f"_{lang}" if lang != "en" else ""

    files: list[Path] = []

    preface = root / "chapterx" / (f"preface{suffix}.md" if suffix else "preface.md")
    if preface.is_file():
        files.append(preface)

    for n in range(1, 13):
        for d in sorted(root.glob(f"chapter{n}-*")):
            if not d.is_dir():
                continue
            name = f"chapter{n}{suffix}.md" if suffix else f"chapter{n}.md"
            md = d / name
            if md.is_file():
                files.append(md)
                break

    appendix = root / "chapterx" / (f"chapterx{suffix}.md" if suffix else "chapterx.md")
    if appendix.is_file():
        files.append(appendix)

    return files


def chapter_html_name(md_path: Path) -> str:
    """Stable HTML filename for a book markdown file."""
    stem = md_path.stem
    parent = md_path.parent.name
    if stem.startswith("preface"):
        return f"{stem}.html"
    m = re.match(r"chapter(\d+)", parent)
    if m:
        return f"chapter{m.group(1).zfill(2)}.html"
    return f"{stem}.html"


def rewrite_chapter_img_paths(html: str, md_path: Path, book_root: Path) -> str:
    """Point img/ at the source chapter folder from flat book_html/."""
    chapter_dir = md_path.parent.resolve()
    try:
        rel = chapter_dir.relative_to(book_root.resolve()).as_posix()
    except ValueError:
        rel = chapter_dir.name
    prefix = f"../{rel}/img/"
    return re.sub(r'src="img/', f'src="{prefix}', html)


def render_book(
    root: Path | str,
    *,
    output_dir: Path | str = "book_html",
    lang: str = "en",
    site_title: str = "",
    theme: str = "default",
    custom_css: Path | None = None,
    mathjax: bool = True,
    include_config: Path | str | None = None,
    processor: MarkdownProcessor | None = None,
) -> dict[str, Any]:
    """Render full book into output_dir with index and prev/next navigation."""
    book_root = Path(root).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    md_files = collect_book_markdown(book_root, lang)
    if not md_files:
        raise FileNotFoundError(f"No chapter markdown found under {book_root} (lang={lang})")

    cfg = include_config or find_peanut_config(book_root)
    proc = processor or MarkdownProcessor(include_config=cfg)
    renderer = BlogRenderer(
        site_title=site_title,
        base_url="",
        theme=theme,
        custom_css=custom_css,
        mathjax=mathjax,
    )
    renderer.copy_static_assets(out_dir, custom_css)

    chapters: list[BookChapter] = []
    processed: list[dict[str, Any]] = []

    for order, md_path in enumerate(md_files):
        result = proc.process_file(md_path)
        if not result:
            continue
        result["content"] = rewrite_chapter_img_paths(
            result["content"], md_path, book_root
        )
        html_name = chapter_html_name(md_path)
        chapters.append(
            BookChapter(
                md_path=md_path,
                html_name=html_name,
                title=result["metadata"]["title"],
                order=order,
            )
        )
        processed.append({**result, "html_name": html_name})

    page_counts = [count_pages(item["content"]) for item in processed]

    built: list[str] = []
    for i, item in enumerate(processed):
        ch = chapters[i]
        prev_ch = chapters[i - 1] if i > 0 else None
        next_ch = chapters[i + 1] if i + 1 < len(chapters) else None
        html = renderer.render_post(
            item,
            book_mode=True,
            prev_href=prev_ch.html_name if prev_ch else None,
            prev_title=prev_ch.title if prev_ch else None,
            next_href=next_ch.html_name if next_ch else None,
            next_title=next_ch.title if next_ch else None,
            prev_chapter_pages=page_counts[i - 1] if i > 0 else 0,
        )
        out_file = out_dir / ch.html_name
        out_file.write_text(html, encoding="utf-8")
        built.append(str(out_file))

    index_html = renderer.render_book_index(
        [
            {"title": c.title, "href": c.html_name, "source": str(c.md_path)}
            for c in chapters
        ],
        site_title=site_title,
    )
    index_path = out_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    built.insert(0, str(index_path))

    return {
        "root": str(book_root),
        "output_dir": str(out_dir),
        "lang": lang,
        "count": len(chapters),
        "built": built,
        "index": str(index_path),
    }
