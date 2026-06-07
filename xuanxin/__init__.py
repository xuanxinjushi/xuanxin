"""xuanxin — Markdown blog to beautiful static HTML."""

from xuanxin._version import BASE_VERSION, __version__, resolve_version
from xuanxin.book import collect_book_markdown, default_book_output_dir, render_book
from xuanxin.builder import BlogBuilder, render_file
from xuanxin.diary import DiaryBuilder
from xuanxin.processor import MarkdownProcessor, process_file, process_string

__all__ = [
    "BASE_VERSION",
    "BlogBuilder",
    "DiaryBuilder",
    "MarkdownProcessor",
    "collect_book_markdown",
    "default_book_output_dir",
    "process_file",
    "process_string",
    "render_book",
    "render_file",
    "resolve_version",
    "__version__",
]
