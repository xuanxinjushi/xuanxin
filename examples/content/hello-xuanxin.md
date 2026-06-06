---
title: "Hello xuanxin"
slug: "hello-xuanxin"
date: "2025-06-06"
author: "xuanxin"
tags: ["intro", "markdown", "static-site"]
description: "Your first post — write Markdown anywhere, get beautiful HTML."
theme: "default"
---

# Hello xuanxin

Write Markdown with **YAML frontmatter**, run one command, and get a static HTML blog.

## Features

- Markdown → HTML with syntax highlighting, tables, TOC
- LaTeX math: inline $E = mc^2$ and display:

$$
\int_0^1 x^2 \, dx = \frac{1}{3}
$$

- YouTube embeds — paste a URL on its own line:

https://youtu.be/dQw4w9WgXcQ

- Image classes: ![small image](https://picsum.photos/400/200){: .img-medium .img-center}

## Code

```python
from xuanxin import BlogBuilder

BlogBuilder(content_dir="content", output_dir="dist").build()
```

## Table

| Feature | Supported |
|---------|-----------|
| Frontmatter | ✅ |
| Custom CSS | ✅ |
| Dark theme | ✅ |

> Customize everything via CSS variables or your own `custom.css`.
