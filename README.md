# xuanxin

Write Markdown blogs anywhere, generate beautiful static HTML with easy style customization.

## Quick start

```bash
cd ~/xuanxin
pip install -e .

# Write posts in examples/content/*.md, then build:
xuanxin build -i examples/content -o examples/dist -t "My Blog"

# Open in browser
python -m http.server 8080 --directory examples/dist
# → http://localhost:8080
```

## Write a post

Create `content/my-post.md`:

```markdown
---
title: "My First Post"
slug: "my-first-post"
date: "2025-06-06"
author: "You"
tags: ["blog"]
description: "A short intro shown on the index page."
theme: "default"          # optional: default | dark | minimal
featured_image_url: "https://example.com/cover.jpg"
---

# Hello World

Your **markdown** content here.

Inline math: $E = mc^2$

https://youtu.be/VIDEO_ID   ← auto-embeds YouTube
```

## Build commands

```bash
# Basic build
xuanxin build -i content/ -o dist/

# Dark theme
xuanxin build -i content/ -o dist/ --theme dark

# Custom CSS (overrides variables & adds rules)
xuanxin build -i content/ -o dist/ --css my-style.css

# Preview HTML body for one file
xuanxin preview content/my-post.md

# List built-in themes
xuanxin themes
```

## Customize styles (3 ways)

### 1. Built-in themes

`default`, `dark`, `minimal` — pass `--theme dark` or set `theme: dark` in frontmatter.

### 2. CSS variables (copy a theme file)

Each theme is just a `:root { ... }` block. Copy `xuanxin/static/themes/default.css` and change colors:

```css
:root {
  --color-primary: #059669;
  --color-bg: #fafafa;
  --font-serif: "Georgia", serif;
  --max-width: 800px;
}
```

Use with `--css my-theme.css`.

### 3. Full custom CSS

Pass any CSS file with `--css`. It loads **after** the base theme, so you can override anything:

```css
:root { --color-primary: hotpink; }
.prose h2 { border-bottom: 2px dashed var(--color-primary); }
.post { box-shadow: none; border: 2px solid black; }
```

See `examples/custom.css` for a gradient-title example.

## Python API

```python
from pathlib import Path
from xuanxin import BlogBuilder, MarkdownProcessor

# Full site build
BlogBuilder(
    content_dir=Path("content"),
    output_dir=Path("dist"),
    site_title="My Blog",
    theme="dark",
    custom_css=Path("custom.css"),
).build()

# Single file MD → HTML
processor = MarkdownProcessor()
result = processor.process_file("content/post.md")
print(result["content"])   # HTML body
print(result["metadata"])  # title, slug, tags, ...
```

## MD → HTML pipeline

1. Parse YAML frontmatter (`python-frontmatter`)
2. Protect LaTeX `$...$` / `$$...$$` from Markdown
3. Convert with Python-Markdown (+ code highlighting, tables, TOC, fenced code)
4. Custom extensions: image CSS classes, YouTube/Vimeo embeds
5. Restore LaTeX (rendered client-side via MathJax in output HTML)
6. Wrap in Jinja2 template → static `.html` files

## Output structure

```
dist/
├── index.html           # post listing
├── manifest.json        # build metadata
├── assets/
│   ├── theme.css        # merged theme + base styles
│   └── custom.css       # your overrides (if --css used)
└── posts/
    ├── my-first-post.html
    └── ...
```

## License

MIT
