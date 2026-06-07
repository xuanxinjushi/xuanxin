#!/usr/bin/env python3
"""CLI for xuanxin — build static HTML from Markdown."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from xuanxin import __version__
from xuanxin.book import default_book_output_dir, discover_book_repo_root, render_book
from xuanxin.builder import BlogBuilder, render_file
from xuanxin.diary import DiaryBuilder
from xuanxin.processor import MarkdownProcessor


def cmd_build(args: argparse.Namespace) -> int:
    custom_css = Path(args.css) if args.css else None
    if custom_css and not custom_css.exists():
        print(f"Warning: custom CSS not found: {custom_css}", file=sys.stderr)

    builder = BlogBuilder(
        content_dir=Path(args.input),
        output_dir=Path(args.output),
        site_title=args.title,
        site_description=args.description,
        base_url=args.base_url,
        theme=args.theme,
        custom_css=custom_css,
        pattern=args.pattern,
        include_drafts=args.include_drafts,
        mathjax=not args.no_mathjax,
    )
    result = builder.build()
    print(f"Built {result['count']} post(s) → {args.output}")
    for path in result["built"]:
        print(f"  ✓ {path}")
    if result["skipped"]:
        print(f"Skipped {len(result['skipped'])} file(s)")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    """Render one .md file, or the full book with --book."""
    custom_css = Path(args.css) if args.css else None
    if custom_css and not custom_css.exists():
        print(f"Warning: custom CSS not found: {custom_css}", file=sys.stderr)

    include_config = Path(args.config) if args.config else None
    if include_config and not include_config.exists():
        print(f"Warning: config not found: {include_config}", file=sys.stderr)

    if args.book:
        root = Path(args.root) if args.root else discover_book_repo_root()
        out_dir = (
            Path(args.output)
            if args.output
            else default_book_output_dir(root, args.lang)
        )
        result = render_book(
            root,
            output_dir=out_dir,
            lang=args.lang,
            site_title=args.title,
            theme=args.theme,
            custom_css=custom_css,
            mathjax=not args.no_mathjax,
            include_config=include_config,
        )
        print(f"Built {result['count']} chapter(s) → {result['output_dir']}")
        for path in result["built"]:
            print(f"  ✓ {path}")
        return 0

    if not args.file:
        print("error: provide a markdown file or use --book", file=sys.stderr)
        return 1

    out_dir = Path(args.output) if args.output else Path.cwd()
    out_file = render_file(
        Path(args.file),
        output_dir=out_dir,
        site_title=args.title,
        theme=args.theme,
        custom_css=custom_css,
        mathjax=not args.no_mathjax,
        include_config=include_config,
    )
    print(f"✓ {out_file}")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    """Convert a single markdown file and print HTML body to stdout."""
    processor = MarkdownProcessor()
    result = processor.process_file(Path(args.file))
    if not result:
        print("Failed to process file", file=sys.stderr)
        return 1
    print(result["content"])
    return 0


def cmd_diary(args: argparse.Namespace) -> int:
    gtag = Path(args.gtag) if args.gtag else None
    if gtag and not gtag.exists():
        print(f"Warning: gtag file not found: {gtag}", file=sys.stderr)

    builder = DiaryBuilder(
        input_dir=Path(args.input),
        output_dir=Path(args.output),
        home_url=args.home,
        gtag_path=gtag,
        site_title=args.title,
        theme=args.theme,
        mathjax=not args.no_mathjax,
        index_page_size=args.page_size,
    )
    result = builder.build()
    pages_note = f", {result['index_pages']} index page(s)" if result["index_pages"] > 1 else ""
    print(f"Built {result['count']} entr{'ies' if result['count'] != 1 else 'y'}{pages_note} → {args.output}")
    for path in result["built"]:
        print(f"  ✓ {path}")
    return 0


def cmd_themes(_args: argparse.Namespace) -> int:
    from xuanxin.renderer import DEFAULT_THEME_DIR

    print("Available themes:")
    for css in sorted(DEFAULT_THEME_DIR.glob("*.css")):
        if css.name.startswith("_"):
            continue
        print(f"  {css.stem}")
    print("\nCustomize: copy a theme file, edit :root variables, pass --css your-theme.css")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="xuanxin",
        description="Write Markdown blogs, generate beautiful static HTML.",
    )
    parser.add_argument("--version", action="version", version=f"xuanxin {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build static site from Markdown files")
    build.add_argument("-i", "--input", default="content", help="Content directory (default: content)")
    build.add_argument("-o", "--output", default="dist", help="Output directory (default: dist)")
    build.add_argument("-t", "--title", default="Blog", help="Site title")
    build.add_argument("-d", "--description", default="", help="Site description")
    build.add_argument("--base-url", default="", help="Base URL prefix for links (e.g. /blog)")
    build.add_argument("--theme", default="default", help="Built-in theme name (default, dark, minimal)")
    build.add_argument("--css", default="", help="Path to custom CSS file (overrides theme vars)")
    build.add_argument("--pattern", default="**/*.md", help="Glob pattern for markdown files")
    build.add_argument("--include-drafts", action="store_true", help="Include draft posts")
    build.add_argument("--no-mathjax", action="store_true", help="Disable MathJax for LaTeX")
    build.set_defaults(func=cmd_build)

    render = sub.add_parser(
        "render",
        help="Render one .md file, or the full book with --book",
    )
    render.add_argument(
        "file",
        nargs="?",
        default="",
        help="Markdown file path (omit with --book)",
    )
    render.add_argument(
        "--book",
        action="store_true",
        help="Render full book (preface, chapters 1–12, appendix) to book_html_{lang}/",
    )
    render.add_argument(
        "--lang",
        default="zh",
        help="Book language suffix: en, zh, tc, jp, sp (default: zh)",
    )
    render.add_argument(
        "--root",
        default="",
        help="Book repository root (default: auto-detect from cwd)",
    )
    render.add_argument(
        "-o",
        "--output",
        default="",
        help="Output directory (default: book_html/ or book_html_{lang}/ for --book)",
    )
    render.add_argument(
        "-t",
        "--title",
        default="",
        help="Site title (optional; shown in header and page title suffix)",
    )
    render.add_argument(
        "--config",
        default="",
        help="Path to peanut.config for conditional includes (default: auto-detect)",
    )
    render.add_argument("--theme", default="default", help="Built-in theme (default, dark, minimal)")
    render.add_argument("--css", default="", help="Path to custom CSS file")
    render.add_argument("--no-mathjax", action="store_true", help="Disable MathJax for LaTeX")
    render.set_defaults(func=cmd_render)

    preview = sub.add_parser("preview", help="Print HTML body for one markdown file")
    preview.add_argument("file", help="Markdown file path")
    preview.set_defaults(func=cmd_preview)

    diary = sub.add_parser("diary", help="Build a flat diary site from dated Markdown files")
    diary.add_argument("-i", "--input", required=True, help="Input folder with .md diary files")
    diary.add_argument("-o", "--output", required=True, help="Output folder for HTML")
    diary.add_argument("-gtag", default="", help="Path to gtag.js snippet to inject in <head>")
    diary.add_argument("-home", default="", help="Home URL for back links (e.g. wu-99.com)")
    diary.add_argument("-t", "--title", default="Diary", help="Diary index title")
    diary.add_argument(
        "--page-size",
        type=int,
        default=20,
        help="Diary entries per index page (default: 20)",
    )
    diary.add_argument("--theme", default="default", help="Built-in theme name (default, dark, minimal)")
    diary.add_argument("--no-mathjax", action="store_true", help="Disable MathJax for LaTeX")
    diary.set_defaults(func=cmd_diary)

    themes = sub.add_parser("themes", help="List available built-in themes")
    themes.set_defaults(func=cmd_themes)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
