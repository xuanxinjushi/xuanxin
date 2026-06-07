"""xuanxin — Markdown blog to beautiful static HTML."""

from xuanxin.book import collect_book_markdown, default_book_output_dir, render_book
from xuanxin.builder import BlogBuilder, render_file
from xuanxin.processor import MarkdownProcessor, process_file, process_string

__version__ = "0.1.1.dev0"
__all__ = [
    "BlogBuilder",
    "MarkdownProcessor",
    "collect_book_markdown",
    "default_book_output_dir",
    "process_file",
    "process_string",
    "render_book",
    "render_file",
    "__version__",
]
