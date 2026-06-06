"""Tests for xuanxin."""

from pathlib import Path

from xuanxin import BlogBuilder, MarkdownProcessor, process_string, render_file


SAMPLE = """---
title: Test Post
slug: test-post
date: 2025-01-01
tags: [a, b]
description: A test
---

# Hello

Inline math $x^2$ and **bold**.

```python
print("hi")
```
"""


def test_process_string():
    result = process_string(SAMPLE)
    assert result["metadata"]["title"] == "Test Post"
    assert result["metadata"]["slug"] == "test-post"
    assert "<h1" in result["content"]
    assert "<strong>bold</strong>" in result["content"]


def test_latex_preserved():
    content = "---\ntitle: Math\n---\n\n$x^2$ and $$\\sum_i x_i$$"
    result = process_string(content)
    assert "$x^2$" in result["content"]
    assert "$$" in result["content"]


def test_build_site(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "post.md").write_text(SAMPLE, encoding="utf-8")

    out = tmp_path / "dist"
    result = BlogBuilder(content_dir=content_dir, output_dir=out, site_title="Test").build()

    assert result["count"] == 1
    assert (out / "index.html").exists()
    assert (out / "posts" / "test-post.html").exists()
    assert (out / "assets" / "theme.css").exists()

    html = (out / "posts" / "test-post.html").read_text(encoding="utf-8")
    assert "Test Post" in html
    assert "Hello" in html


def test_render_single_file(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    md = content_dir / "the-serendipity-of-language.md"
    md.write_text(SAMPLE, encoding="utf-8")

    work_dir = tmp_path / "work"
    work_dir.mkdir()
    out = render_file(md, output_dir=work_dir, site_title="Test")

    assert out == work_dir / "the-serendipity-of-language.html"
    assert out.exists()
    assert (work_dir / "assets" / "theme.css").exists()
    html = out.read_text(encoding="utf-8")
    assert 'href="assets/theme.css"' in html
    assert "Test Post" in html


def test_youtube_embed():
    md = "---\ntitle: Video\n---\n\nhttps://youtu.be/dQw4w9WgXcQ\n"
    result = process_string(md)
    assert "iframe" in result["content"]
    assert "dQw4w9WgXcQ" in result["content"]
