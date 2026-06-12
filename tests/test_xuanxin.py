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
    assert 'class="math-display"' in result["content"]
    assert "$$\\sum_i x_i$$" in result["content"]
    assert "<p>$$" not in result["content"]


def test_autolink_bare_url():
    md = (
        "---\ntitle: Links\n---\n\n"
        "- **CGFM** — example — https://arxiv.org/abs/2507.07192\n\n"
        "See https://math4ai.org/ for more.\n"
    )
    result = process_string(md)
    html = result["content"]
    assert 'href="https://arxiv.org/abs/2507.07192"' in html
    assert 'href="https://math4ai.org/"' in html


def test_autolink_skips_code_and_math():
    md = (
        "---\ntitle: Skip\n---\n\n"
        "`https://example.com/a` and $https://example.com/b$\n\n"
        "```\nhttps://example.com/c\n```\n"
    )
    result = process_string(md)
    html = result["content"]
    assert html.count('href="https://example.com/a"') == 0
    assert html.count('href="https://example.com/b"') == 0
    assert html.count('href="https://example.com/c"') == 0


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
    assert 'class="image-background-section image-background-bottom-right"' in html
    assert "bottom: 1.0in" in html
    assert '<figure class="image-block">' in html
    assert "<figcaption>A caption</figcaption>" in html


def test_unwrap_fullpage_from_paragraph():
    html = process_string("![](img/cover.jpg){.fullpage}\n")["content"]
    assert '<p><div class="fullpage-image">' not in html
    assert '<div class="fullpage-image">' in html


def test_fullpage_height_percent_preserved_on_image():
    html = process_string("![](img/a.jpg){.fullpage height=40%}\n")["content"]
    assert "height: 40%" in html
    assert "max-height:" not in html


def test_bottom_right_background_keeps_adjacent_paragraphs_together():
    md = """## 泉水

村子不大，

![](img/quan.jpg){.background .bottom-right alpha=0.3 width=40% bottom-offset=1.0in}

十几户人家。
"""
    html = process_string(md)["content"]
    assert "image-background-bottom-right" in html
    assert html.index("村子不大") < html.index("quan.jpg") < html.index("十几户人家")
    # Both paragraphs live in the same background wrapper (not split across blocks).
    section_start = html.index('class="image-background-section image-background-bottom-right"')
    section_end = html.index("</div>", section_start)
    section = html[section_start:section_end]
    assert "村子不大" in section
    assert "十几户人家" in section
    assert section.count("<p>") == 2


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


def test_footnotes_before_chapter_poster():
    from xuanxin.footnotes import reorder_footnotes_before_chapter_poster

    wrong = (
        '<p>Body.</p>'
        '<div class="xuanxin-pagebreak"></div>'
        '<p><div class="fullpage-image"><img src="img/p.jpg" class="fullpage" /></div></p>'
        '<div class="footnote"><hr /><ol><li id="fn:1"><p>Note.</p></li></ol></div>'
    )
    fixed = reorder_footnotes_before_chapter_poster(wrong)
    assert fixed.index("footnote") < fixed.index("p.jpg")

    chapter = Path(__file__).resolve().parents[2] / "chapter1-shan" / "chapter1_zh.md"
    if chapter.is_file():
        result = MarkdownProcessor().process_file(chapter)
        content = result["content"]
        assert "footnote" in content
        assert "p.jpg" in content
        assert content.index("footnote") < content.index("p.jpg")


def test_note_sections():
    sample = """# Reviews

>NOTES: __特蕾西（硅谷初创公司联合创始人）__

不可思议的旅程！非常富有哲理。

>NOTEE

>IMPORS: Key point here.

>IMPORE

>WARNS: Watch out for this.

>WARNE
"""
    content = process_string(sample)["content"]
    assert "NOTES:" not in content
    assert "NOTEE" not in content
    assert 'class="xuanxin-notesection"' in content
    assert 'class="xuanxin-importantsection"' in content
    assert 'class="xuanxin-warnsection"' in content
    assert "特蕾西" in content
    assert "不可思议的旅程" in content
    assert "Key point here" in content
    assert "Watch out for this" in content

    review = Path(__file__).resolve().parents[2] / "chapterx" / "review_zh.md"
    if review.is_file():
        review_html = MarkdownProcessor().process_file(review)["content"]
        assert "NOTES:" not in review_html
        assert "NOTEE" not in review_html
        assert review_html.count('class="xuanxin-notesection"') >= 6
        assert "特蕾西" in review_html


def test_gallery_sections():
    import hashlib

    sample = """# Day out

>GALLERYS

![](img/a.jpg)
![500 USD](img/b.jpg)
![With the painter](img/c.jpg)

>GALLERYE

After gallery.
"""
    content = process_string(sample)["content"]
    assert "GALLERYS" not in content
    assert "GALLERYE" not in content
    assert "xuanxin-gallery" in content
    assert "data-gallery-prev" in content
    assert "data-gallery-next" in content
    assert content.count("xuanxin-gallery-slide") == 3
    assert 'src="img/a.jpg"' in content
    assert 'src="img/b.jpg"' in content
    assert "xuanxin-gallery-has-captions" in content
    assert 'data-caption="500 USD"' in content
    assert 'data-caption="With the painter"' in content
    assert "data-gallery-caption-bar" in content
    assert ">500 USD</button>" not in content
    assert "After gallery." in content

    single = process_string(">GALLERYS\n\n![](img/only.jpg)\n\n>GALLERYE\n")["content"]
    assert "xuanxin-gallery-single" in single
    assert "xuanxin-gallery-controls" not in single
    assert "data-gallery-prev" not in single

    locked = process_string(
        ">GALLERYS password: xuanxin\n\n![](img/a.jpg)\n\n>GALLERYE\n"
    )["content"]
    assert "data-gallery-lock" in locked
    assert "data-gallery-unlock" in locked
    assert "password: xuanxin" not in locked
    assert f'data-gallery-password-hash="{hashlib.sha256(b"xuanxin").hexdigest()}"' in locked
    assert 'data-gallery hidden' in locked or "data-gallery hidden>" in locked

    video = process_string(">GALLERYS\n\n![](clip/demo.mp4)\n\n>GALLERYE\n")["content"]
    assert "xuanxin-gallery-video" in video
    assert 'src="clip/demo.mp4"' in video

    diary = Path("/home/wukong/xx-diary/20260607.md")
    if diary.is_file():
        html = MarkdownProcessor().process_file(diary)["content"]
        assert "GALLERYS" not in html
        assert "GALLERYE" not in html
        assert "xuanxin-gallery" in html
        assert html.count("xuanxin-gallery-slide") >= 10


def test_section_nav():
    md = """# Chapter 4: 火 {-}

*篝火、烛火、火锅*

> quote

## 篝火

Section one.

## 烛火

Section two.

## 火锅

Section three.
"""
    html = process_string(md)["content"]
    assert 'class="xuanxin-section-nav"' in html
    assert 'class="xuanxin-section-nav-btn"' in html
    assert 'href="#_' in html
    assert ">篝火</a>" in html
    assert ">烛火</a>" in html
    assert ">火锅</a>" in html
    assert "<p><em>篝火" not in html

    ch4 = Path(__file__).resolve().parents[2] / "chapter4-huo" / "chapter4_zh.md"
    if ch4.is_file():
        ch4_html = MarkdownProcessor().process_file(ch4)["content"]
        assert 'class="xuanxin-section-nav"' in ch4_html
        assert ch4_html.count("xuanxin-section-nav-btn") == 3


def test_conditional_include_if_true(tmp_path):
    snippet = tmp_path / "snippet.md"
    snippet.write_text("Included paragraph.\n", encoding="utf-8")
    md = tmp_path / "chapter.md"
    md.write_text(
        "Before.\n\n<!-- include: snippet.md if true -->\n\nAfter.\n",
        encoding="utf-8",
    )
    result = MarkdownProcessor().process_file(md)
    assert "Included paragraph." in result["raw_content"]
    assert "include:" not in result["raw_content"]
    assert "Included paragraph." in result["content"]


def test_conditional_include_if_false(tmp_path):
    snippet = tmp_path / "snippet.md"
    snippet.write_text("Hidden.\n", encoding="utf-8")
    md = tmp_path / "chapter.md"
    md.write_text("<!-- include: snippet.md if enable_chapter_end_poster -->\n", encoding="utf-8")
    (tmp_path / "peanut.config").write_text(
        '{"enable_chapter_end_poster": false}', encoding="utf-8"
    )
    result = MarkdownProcessor(include_config=tmp_path / "peanut.config").process_file(md)
    assert "Hidden." not in result["raw_content"]
    assert "include:" not in result["raw_content"]


def test_conditional_include_from_peanut_config(tmp_path):
    snippets = tmp_path / "snippets"
    snippets.mkdir()
    (snippets / "poster.md").write_text(
        "\\newpage\n\n![](img/p.jpg){.fullpage}\n", encoding="utf-8"
    )
    chapter_dir = tmp_path / "chapter1-shan"
    chapter_dir.mkdir()
    (chapter_dir / "chapter1_zh.md").write_text(
        "# Chapter 1\n\nEnd.\n\n"
        "<!-- include: ../snippets/poster.md if enable_chapter_end_poster -->\n",
        encoding="utf-8",
    )
    (tmp_path / "peanut.config").write_text(
        '{"enable_chapter_end_poster": true}', encoding="utf-8"
    )
    result = MarkdownProcessor(include_config=tmp_path / "peanut.config").process_file(
        chapter_dir / "chapter1_zh.md"
    )
    assert "include:" not in result["raw_content"]
    assert "img/p.jpg" in result["raw_content"]
    assert "fullpage" in result["content"] or "fullpage-image" in result["content"]


def test_multiple_backgrounds_do_not_overlap():
    md = """---
title: Preface
---

# 前言

Intro.

![](img/ren.jpg){.background alpha=0.03 width=40%}

Middle text.

我对“美”的最早记忆，

是雪。

![](img/mei.jpg){.background alpha=0.03 height=40%}
"""
    html = process_string(md)["content"]
    assert "position: fixed" not in html
    assert "image-background-stack" in html
    assert html.count("image-background-stack-item") == 2
    assert 'data-bg-count="2"' in html
    assert html.index("ren.jpg") < html.index("mei.jpg")
    assert html.index("Middle text.") < html.index("mei.jpg")


def test_preface_two_backgrounds_balanced():
    preface = Path(__file__).resolve().parents[2] / "chapterx" / "preface_zh.md"
    if not preface.is_file():
        import pytest

        pytest.skip("preface_zh.md not found")
    html = process_string(preface.read_text(encoding="utf-8"))["content"]
    stack_start = html.index('class="image-background-stack"')
    stack_end = html.index("</div></div>", stack_start) + len("</div></div>")
    stack = html[stack_start:stack_end]
    items = stack.split("image-background-stack-item")
    assert len(items) == 3  # leading + 2 items
    assert "那是断奶" in items[1]
    assert "我对“美”" in items[2]
    assert "那是断奶" not in items[2]


def test_three_backgrounds_equal_stack():
    md = """---
title: Test
---

# Section

A.

![](img/a.jpg){.background alpha=0.03}

Text A.

![](img/b.jpg){.background alpha=0.03}

Text B.

![](img/c.jpg){.background alpha=0.03}
"""
    html = process_string(md)["content"]
    assert 'data-bg-count="3"' in html
    assert 'class="image-background-stack"' in html
    assert html.count("image-background-stack-item") == 3
    assert html.index("a.jpg") < html.index("b.jpg") < html.index("c.jpg")


def test_background_sections_respect_pagebreak_and_h1():
    from xuanxin.paginate import PAGE_BREAK_RE, paginate_content

    md = """---
title: Test Preface
---

## Section

Intro.

![](img/x2.jpg){.background .bottom-right alpha=0.03 width=20%}

\\newpage

![](img/me.jpg){.fullpage width=30%}

\\newpage

# 前言

Para one.

![](img/ren.jpg){.background alpha=0.03 width=40%}

Para two.
"""
    html = process_string(md)["content"]
    parts = PAGE_BREAK_RE.split(html)
    assert len(parts) == 3
    assert "Para one." in parts[2]
    assert "ren.jpg" in parts[2]
    assert "Para two." in parts[2]
    assert not parts[2].lstrip().startswith("</div>")
    for part in parts:
        assert part.count("<div") == part.count("</div>"), part[:80]

    paginated, page_count = paginate_content(html)
    assert page_count == 3
    assert 'data-page="3"' in paginated
    assert paginated.count("前言") >= 1
    page3 = paginated.split('data-page="3"')[1]
    assert "Para one." in page3
    assert "Para two." in page3
    assert "ren.jpg" in page3


def test_paginate_content():
    from xuanxin.paginate import count_pages, paginate_content

    html = "<p>One</p><div class=\"xuanxin-pagebreak\"></div><p>Two</p>"
    assert count_pages(html) == 2
    paginated, n = paginate_content(html)
    assert n == 2
    assert "xuanxin-paginated-reader" in paginated
    assert 'data-page="1"' in paginated
    assert 'data-page="2"' in paginated
    assert paginated.count("xuanxin-page") == 2


def test_render_paginated_chapter(tmp_path):
    md = tmp_path / "preface.md"
    md.write_text(
        "![](img/cover.jpg){.fullpage}\n\n\\newpage\n\n# Title\n\nPage two.\n",
        encoding="utf-8",
    )
    out = render_file(md, output_dir=tmp_path)
    html = out.read_text(encoding="utf-8")
    assert "xuanxin-paginated-reader" in html
    assert "page-reader.js" in html
    assert "page-nav" in html
    assert r"\newpage" not in html


def test_latex_fenced_block_stripped():
    md = """# Title

Visible text.

```{=latex}
% END_OF_PREFACE
```

Still here.

```{=latex}
\\thispagestyle{empty}
\\begin{center}
Signature
\\end{center}
```

The end.
"""
    html = process_string(md)["content"]
    assert "END_OF_PREFACE" not in html
    assert "thispagestyle" not in html
    assert "<pre>" not in html
    assert "Visible text." in html
    assert "Still here." in html
    assert "The end." in html


def test_latex_pagebreak():
    md = """# Title

Before.

\\newpage

After.

\\clearpage

End.
"""
    html = process_string(md)["content"]
    assert r"\newpage" not in html
    assert r"\clearpage" not in html
    assert "xuanxin-pagebreak" in html
    assert html.count("xuanxin-pagebreak") == 2
    assert "Before." in html
    assert "After." in html
    assert "End." in html


def test_title_from_first_h1_after_leading_content():
    md = """![](img/cover.jpg){.fullpage}

# 云层之上 (Above The Clouds)

Body.
"""
    result = process_string(md)
    assert result["metadata"]["title"] == "云层之上 (Above The Clouds)"
    assert "<h1" not in result["content"]
    assert "Body." in result["content"]


def test_collect_book_markdown():
    from xuanxin.book import collect_book_markdown, discover_book_repo_root, is_book_repo_root

    cur = Path(__file__).resolve().parent
    root = None
    while cur != cur.parent:
        if is_book_repo_root(cur):
            root = cur
            break
        cur = cur.parent
    if root is None:
        import pytest

        pytest.skip("book repo not found")

    files = collect_book_markdown(root, lang="zh")
    assert len(files) >= 2
    assert files[0].name == "preface_zh.md"
    assert files[-1].name == "chapterx_zh.md"
    assert any(f.parent.name == "chapter1-shan" for f in files)


def test_default_book_output_dir():
    from xuanxin.book import default_book_output_dir

    root = Path("/repo")
    assert default_book_output_dir(root, "en") == Path("/repo/book_html")
    assert default_book_output_dir(root, "zh") == Path("/repo/book_html_zh")
    assert default_book_output_dir(root, "cn") == Path("/repo/book_html_zh")
    assert default_book_output_dir(root, "tc") == Path("/repo/book_html_tc")
    assert default_book_output_dir(root, "jp") == Path("/repo/book_html_jp")
    assert default_book_output_dir(root, "sp") == Path("/repo/book_html_sp")


def test_render_book(tmp_path):
    from xuanxin.book import render_book

    root = tmp_path / "book"
    (root / "chapterx").mkdir(parents=True)
    (root / "chapter1-shan").mkdir()
    (root / "chapter2-lu").mkdir()
    (root / "chapterx" / "preface_zh.md").write_text(
        "# Preface\n\nPreface text.\n", encoding="utf-8"
    )
    (root / "chapter1-shan" / "chapter1_zh.md").write_text(
        "# Chapter 1\n\n![](img/a.jpg)\n", encoding="utf-8"
    )
    (root / "chapter2-lu" / "chapter2_zh.md").write_text(
        "# Chapter 2\n\nSecond chapter.\n", encoding="utf-8"
    )
    (root / "chapterx" / "chapterx_zh.md").write_text(
        "# Appendix\n\nEnd matter.\n", encoding="utf-8"
    )

    out = tmp_path / "book_html"
    result = render_book(root, output_dir=out, lang="zh", site_title="Test Book")
    assert result["count"] == 4
    assert (out / "index.html").exists()
    assert (out / "preface_zh.html").exists()
    assert (out / "chapter01.html").exists()
    assert (out / "chapter02.html").exists()
    assert (out / "chapterx_zh.html").exists()

    ch1 = (out / "chapter01.html").read_text(encoding="utf-8")
    assert 'src="../chapter1-shan/img/a.jpg"' in ch1
    assert "chapter-nav" in ch1
    assert 'href="preface_zh.html"' in ch1
    assert 'href="chapter02.html"' in ch1
    assert 'href="index.html"' in ch1

    ch2 = (out / "chapter02.html").read_text(encoding="utf-8")
    assert 'href="chapter01.html"' in ch2
    assert 'href="chapterx_zh.html"' in ch2

    index = (out / "index.html").read_text(encoding="utf-8")
    assert "Test Book" in index
    assert "Preface" in index
    assert "Chapter 2" in index

    default_out = root / "book_html_zh"
    result_default = render_book(root, lang="zh", site_title="Test Book")
    assert result_default["output_dir"] == str(default_out.resolve())
    assert default_out.exists()
    assert (default_out / "index.html").exists()


def test_dev_version_uses_git_commit_hash():
    from xuanxin import __version__
    from xuanxin._version import git_commit_hash, resolve_version

    assert resolve_version("0.1.1") == "0.1.1"
    assert resolve_version("1.0.0") == "1.0.0"

    commit = git_commit_hash()
    if commit is None:
        import pytest

        pytest.skip("git commit hash unavailable")
    assert resolve_version("0.1.1.dev0") == commit

    from xuanxin._version import BASE_VERSION

    if ".dev" in BASE_VERSION:
        assert __version__ == commit
    else:
        assert __version__ == BASE_VERSION


def test_date_from_stem():
    from datetime import datetime

    from xuanxin.diary import date_from_stem, normalize_home_url

    assert date_from_stem("20260506") == datetime(2026, 5, 6)
    assert date_from_stem("not-a-date") is None
    assert normalize_home_url("wu-99.com") == "https://wu-99.com"
    assert normalize_home_url("https://example.com") == "https://example.com"


def test_build_diary(tmp_path):
    from xuanxin.diary import DiaryBuilder

    input_dir = tmp_path / "diary_md"
    input_dir.mkdir()
    (input_dir / "20260506.md").write_text("# Morning walk\n\nSunny day.\n", encoding="utf-8")
    (input_dir / "20260516.md").write_text(
        "---\ntitle: Late spring\n---\n\nRainy afternoon.\n", encoding="utf-8"
    )

    gtag = tmp_path / "gtag.js"
    gtag.write_text("<!-- gtag -->\n", encoding="utf-8")

    out = tmp_path / "diary_html"
    result = DiaryBuilder(
        input_dir=input_dir,
        output_dir=out,
        home_url="wu-99.com",
        gtag_path=gtag,
        site_title="My Diary",
    ).build()

    assert result["count"] == 2
    assert (out / "index.html").exists()
    assert (out / "20260506.html").exists()
    assert (out / "20260516.html").exists()
    assert (out / "assets" / "theme.css").exists()

    index = (out / "index.html").read_text(encoding="utf-8")
    assert "My Diary" in index
    assert 'href="20260506.html"' in index
    assert 'href="20260516.html"' in index
    assert 'href="https://wu-99.com"' in index
    assert "<!-- gtag -->" in index

    entry = (out / "20260506.html").read_text(encoding="utf-8")
    assert "Morning walk" in entry
    assert 'href="https://wu-99.com"' in entry
    assert 'href="index.html"' in entry
    assert "Next day →" in entry
    assert "← Previous day" not in entry
    assert "<!-- gtag -->" in entry


def test_diary_index_pagination(tmp_path):
    from xuanxin.diary import DiaryBuilder, diary_index_filename

    input_dir = tmp_path / "diary_md"
    input_dir.mkdir()
    for day in range(1, 26):
        (input_dir / f"202601{day:02d}.md").write_text(f"# Day {day}\n\nEntry {day}.\n", encoding="utf-8")

    out = tmp_path / "diary_html"
    result = DiaryBuilder(
        input_dir=input_dir,
        output_dir=out,
        home_url="wu-99.com",
        index_page_size=10,
    ).build()

    assert result["count"] == 25
    assert result["index_pages"] == 3
    assert (out / "index.html").exists()
    assert (out / "index-2.html").exists()
    assert (out / "index-3.html").exists()

    page1 = (out / "index.html").read_text(encoding="utf-8")
    assert "page 1 of 3" in page1
    assert 'href="20260125.html"' in page1
    assert 'href="index-2.html"' in page1
    assert "Older →" in page1
    assert "← Newer" not in page1

    page2 = (out / "index-2.html").read_text(encoding="utf-8")
    assert 'href="index.html"' in page2
    assert 'href="index-3.html"' in page2
    assert "← Newer" in page2
    assert "Older →" in page2

    page3 = (out / "index-3.html").read_text(encoding="utf-8")
    assert 'href="20260101.html"' in page3
    assert 'href="index-2.html"' in page3
    assert "Older →" not in page3

    assert diary_index_filename(1) == "index.html"
    assert diary_index_filename(2) == "index-2.html"


def test_diary_copies_local_images(tmp_path):
    from xuanxin.diary import DiaryBuilder

    input_dir = tmp_path / "diary_md"
    img_dir = input_dir / "20260607"
    img_dir.mkdir(parents=True)
    (img_dir / "photo.jpg").write_bytes(b"fake-jpeg")
    (input_dir / "20260607.md").write_text(
        "# Day out\n\n"
        ">GALLERYS\n\n"
        "![](20260607/photo.jpg)\n\n"
        ">GALLERYE\n",
        encoding="utf-8",
    )

    out = tmp_path / "diary_html"
    result = DiaryBuilder(input_dir=input_dir, output_dir=out).build()

    assert result["count"] == 1
    assert (out / "20260607" / "photo.jpg").exists()
    assert (out / "20260607" / "photo.jpg").read_bytes() == b"fake-jpeg"
    html = (out / "20260607.html").read_text(encoding="utf-8")
    assert 'src="20260607/photo.jpg"' in html


def test_diary_converts_large_png_to_jpg(tmp_path):
    import os

    from PIL import Image

    from xuanxin.diary import DiaryBuilder

    input_dir = tmp_path / "diary_md"
    img_dir = input_dir / "19890602"
    img_dir.mkdir(parents=True)
    png_path = img_dir / "n.png"
    Image.frombytes("RGBA", (900, 900), os.urandom(900 * 900 * 4)).save(png_path, format="PNG")
    assert png_path.stat().st_size > 100 * 1024

    (input_dir / "19890602.md").write_text(
        "# Old photo\n\n![](19890602/n.png)\n",
        encoding="utf-8",
    )

    out = tmp_path / "diary_html"
    DiaryBuilder(input_dir=input_dir, output_dir=out).build()

    assert not (out / "19890602" / "n.png").exists()
    jpg_path = out / "19890602" / "n_small.jpg"
    assert jpg_path.exists()
    assert jpg_path.stat().st_size > 0

    source_jpg = input_dir / "19890602" / "n_small.jpg"
    assert source_jpg.exists()
    assert source_jpg.stat().st_size > 0

    html = (out / "19890602_zh.html").read_text(encoding="utf-8")
    assert 'src="19890602/n_small.jpg"' in html
    assert 'src="19890602/n.png"' not in html


def test_diary_normalizes_wrong_asset_folder_and_rewrites_png(tmp_path):
    import os

    from PIL import Image

    from xuanxin.diary import DiaryBuilder

    input_dir = tmp_path / "diary_md"
    img_dir = input_dir / "19890602"
    img_dir.mkdir(parents=True)
    png_path = img_dir / "n.png"
    Image.frombytes("RGBA", (900, 900), b"\0" * (900 * 900 * 4)).save(png_path, format="PNG")
    if png_path.stat().st_size <= 100 * 1024:
        Image.frombytes("RGBA", (1200, 900), os.urandom(1200 * 900 * 4)).save(png_path, format="PNG")

    (input_dir / "19890602.md").write_text(
        "# Typo path\n\n"
        ">GALLERYS\n\n"
        "![](191890602/n.png)\n\n"
        ">GALLERYE\n",
        encoding="utf-8",
    )

    out = tmp_path / "diary_html"
    DiaryBuilder(input_dir=input_dir, output_dir=out).build()

    html = (out / "19890602_zh.html").read_text(encoding="utf-8")
    assert 'src="19890602/n_small.jpg"' in html
    assert "191890602/n.png" not in html
    assert (input_dir / "19890602" / "n_small.jpg").exists()


def test_diary_uses_existing_small_jpg_when_markdown_refs_png(tmp_path):
    from xuanxin.diary import DiaryBuilder, normalize_diary_asset_refs

    input_dir = tmp_path / "diary_md"
    img_dir = input_dir / "19890602"
    img_dir.mkdir(parents=True)
    (img_dir / "n_small.jpg").write_bytes(b"existing-jpeg")
    (input_dir / "19890602.md").write_text("# Photo\n\n![](19890602/n.png)\n", encoding="utf-8")

    normalized = normalize_diary_asset_refs(
        (input_dir / "19890602.md").read_text(encoding="utf-8"),
        "19890602",
        input_dir,
    )
    assert "![](19890602/n_small.jpg)" in normalized
    assert "n.png" not in normalized

    out = tmp_path / "diary_html"
    DiaryBuilder(input_dir=input_dir, output_dir=out).build()
    html = (out / "19890602_zh.html").read_text(encoding="utf-8")
    assert 'src="19890602/n_small.jpg"' in html
    assert (out / "19890602" / "n_small.jpg").read_bytes() == b"existing-jpeg"


def test_diary_removes_stale_index_pages(tmp_path):
    from xuanxin.diary import DiaryBuilder

    input_dir = tmp_path / "diary_md"
    input_dir.mkdir()
    out = tmp_path / "diary_html"

    for day in range(1, 26):
        (input_dir / f"202601{day:02d}.md").write_text(f"# Day {day}\n", encoding="utf-8")
    DiaryBuilder(input_dir=input_dir, output_dir=out, index_page_size=10).build()
    assert (out / "index-3.html").exists()

    for path in input_dir.glob("*.md"):
        if path.stem not in ("20260101", "20260102"):
            path.unlink()
    DiaryBuilder(input_dir=input_dir, output_dir=out, index_page_size=10).build()
    assert (out / "index.html").exists()
    assert not (out / "index-2.html").exists()
    assert not (out / "index-3.html").exists()


def test_diary_bilingual_and_day_nav(tmp_path):
    from xuanxin.diary import DiaryBuilder

    input_dir = tmp_path / "diary_md"
    input_dir.mkdir()
    (input_dir / "20260608.md").write_text("# English day\n\nHello.\n", encoding="utf-8")
    (input_dir / "20260608_zh.md").write_text("# 中文日\n\n你好。\n", encoding="utf-8")
    (input_dir / "20260609.md").write_text("# Next day\n\nLater.\n", encoding="utf-8")
    (input_dir / "20260609_zh.md").write_text("# 下一天\n\n稍后。\n", encoding="utf-8")

    out = tmp_path / "diary_html"
    DiaryBuilder(input_dir=input_dir, output_dir=out).build()

    en = (out / "20260608.html").read_text(encoding="utf-8")
    zh = (out / "20260608_zh.html").read_text(encoding="utf-8")
    assert 'class="lang-toggle"' in en
    assert 'href="20260608_zh.html"' in en
    assert "中文" in en
    assert 'href="20260608.html"' in zh
    assert "English" in zh
    assert "全部日记" in zh
    assert "日记目录" in zh
    assert 'lang="zh-Hans"' in zh
    assert 'href="20260609.html"' in en
    assert "Next day →" in en
    assert "← Previous day" not in en
    assert 'href="20260608.html"' in (out / "20260609.html").read_text(encoding="utf-8")

    zh_next = (out / "20260609_zh.html").read_text(encoding="utf-8")
    assert "← 前一天" in zh_next
    assert 'href="20260608_zh.html"' in zh_next
    assert "目录" in zh_next

    index = (out / "index.html").read_text(encoding="utf-8")
    assert index.count("20260608") >= 1
    assert "data-diary-lang-toggle" in index
    assert 'class="lang-toggle"' in index
    assert "data-lang-entries" in index
    assert "data-diary-entry-title" in index
    assert "diary-index-langs" not in index
    assert "diary-lang-switch" not in index


def test_diary_encrypts_locked_gallery_assets(tmp_path):
    from xuanxin.diary import DiaryBuilder
    from xuanxin.gallery_crypto import decrypt_bytes, encrypt_bytes

    input_dir = tmp_path / "diary_md"
    asset_dir = input_dir / "20260610"
    asset_dir.mkdir(parents=True)
    secret = asset_dir / "secret.jpg"
    secret.write_bytes(b"secret-image-bytes")

    (input_dir / "20260610.md").write_text(
        "# Locked\n\n>GALLERYS password: testpass\n\n![](20260610/secret.jpg)\n\n>GALLERYE\n",
        encoding="utf-8",
    )

    out = tmp_path / "diary_html"
    DiaryBuilder(input_dir=input_dir, output_dir=out).build()

    enc_path = out / "20260610" / "secret.jpg.enc"
    plain_path = out / "20260610" / "secret.jpg"
    assert enc_path.is_file()
    assert not plain_path.is_file()

    html = (out / "20260610.html").read_text(encoding="utf-8")
    assert 'data-encrypted-src="20260610/secret.jpg.enc"' in html
    assert 'src="20260610/secret.jpg"' not in html
    assert "secret-image-bytes" not in html

    payload = enc_path.read_bytes()
    assert payload[:8] == b"xuanxin1"
    assert decrypt_bytes(payload, "testpass") == b"secret-image-bytes"


def test_diary_entry_password_frontmatter(tmp_path):
    import hashlib

    from xuanxin.diary import DiaryBuilder

    input_dir = tmp_path / "diary_md"
    input_dir.mkdir(parents=True)
    (input_dir / "20260611_zh.md").write_text(
        "---\ntitle: Secret day\npassword: xuanxin\n---\n\n# Hidden\n\nSecret body $x^2$.\n",
        encoding="utf-8",
    )

    out = tmp_path / "diary_html"
    DiaryBuilder(input_dir=input_dir, output_dir=out).build()

    html = (out / "20260611_zh.html").read_text(encoding="utf-8")
    expected_hash = hashlib.sha256(b"xuanxin").hexdigest()
    assert 'data-entry-lock' in html
    assert f'data-entry-password-hash="{expected_hash}"' in html
    assert "Secret body" in html
    assert 'data-entry-body hidden' in html
    assert "篇目密码" in html


def test_gallery_crypto_roundtrip():
    import pytest
    from cryptography.exceptions import InvalidTag

    from xuanxin.gallery_crypto import decrypt_bytes, encrypt_bytes

    plain = b"hello encrypted world"
    blob = encrypt_bytes(plain, "pw")
    assert blob.startswith(b"xuanxin1")
    assert decrypt_bytes(blob, "pw") == plain
    with pytest.raises(InvalidTag):
        decrypt_bytes(blob, "wrong")
