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


def test_tp_image_and_bubble_image_attrs():
    md = """---
title: Chapter
---

# Chapter 1

**tp_image**

![](img/shan.jpg){width=75% alpha=0.8}

## Section

Intro.

![](img/quan.jpg){.background .bottom-right alpha=0.3 width=40% bottom-offset=1.0in}

More text.

## Next

After.

![A caption](img/x.jpg){.block width=80% align=center}
"""
    html = process_string(md)["content"]
    assert "tp_image" not in html
    assert "tp-image" in html
    assert "tp-image-section" in html
    assert 'src="img/shan.jpg"' in html
    assert "opacity: 0.8" in html
    assert "width: 75%" in html
    assert "background" in html
    assert "bottom-right" in html
    assert "position: absolute" in html
    assert "position: fixed" not in html
    assert 'class="image-background-section"' in html
    assert "bottom: 1.0in" in html
    assert '<figure class="image-block">' in html
    assert "<figcaption>A caption</figcaption>" in html


def test_inject_tp_image_class():
    from xuanxin.image_attrs import inject_tp_image_class

    assert inject_tp_image_class("![](img/a.jpg){width=50%}") == "![](img/a.jpg){.tp-image width=50%}"
    assert inject_tp_image_class("![](img/a.jpg)") == "![](img/a.jpg){.tp-image}"


def test_backslash_blank_line():
    md = """---
title: Breaks
---

第一行。

\\
第二行。

第三行。
"""
    html = process_string(md)["content"]
    assert "xuanxin-blank" in html
    assert "<p>\\" not in html
    assert '<div class="xuanxin-blank"' in html
    assert "<p>第二行。" in html
    assert html.index("xuanxin-blank") < html.index("第二行")


def test_title_from_first_h1_without_frontmatter():
    md = """# Chapter 1: 山 {-}

*泉水、泥土、石头*

正文。
"""
    result = process_string(md)
    assert result["metadata"]["title"] == "Chapter 1: 山"
    assert "<h1" not in result["content"]
    assert "泉水、泥土、石头" in result["content"]
    assert "正文。" in result["content"]


def test_render_chapter_without_blog_title(tmp_path):
    md = tmp_path / "chapter1_zh.md"
    md.write_text("# Chapter 1: 山 {-}\n\n正文。\n", encoding="utf-8")
    out = render_file(md, output_dir=tmp_path)
    html = out.read_text(encoding="utf-8")
    assert "<title>Chapter 1: 山</title>" in html
    assert "Blog" not in html
    assert "site-header" not in html
