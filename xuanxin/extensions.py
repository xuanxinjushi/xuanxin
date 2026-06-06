"""Markdown extensions: image classes, video embeds."""

from __future__ import annotations

import re

from markdown.extensions import Extension
from markdown.inlinepatterns import IMAGE_LINK_RE, ImageInlineProcessor
from markdown.preprocessors import Preprocessor


class ImageWithClassesProcessor(ImageInlineProcessor):
    """Support CSS classes on images via {: .class1 .class2} syntax."""

    def handleMatch(self, m, data):
        img = super().handleMatch(m, data)
        if img is None:
            return None, None, None

        class_match = re.search(r"\{\:\s*([^}]+)\}", m.group(0))
        if class_match:
            classes = class_match.group(1).strip().split()
            existing = img.attrib.get("class", "").split()
            img.attrib["class"] = " ".join(existing + classes)

        return img, m.start(0), m.end(0)


class ImageClassesExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(
            ImageWithClassesProcessor(IMAGE_LINK_RE, md), "image", 150
        )


class VideoEmbedPreprocessor(Preprocessor):
    """Convert standalone video URLs (YouTube, Vimeo) to responsive embeds."""

    PATTERNS = [
        (
            "youtube",
            [
                r"^https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11}).*$",
                r"^https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11}).*$",
                r"^https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11}).*$",
            ],
            "https://www.youtube.com/embed/{id}",
        ),
        (
            "vimeo",
            [
                r"^https?://(?:www\.)?vimeo\.com/([0-9]+).*$",
                r"^https?://(?:www\.)?vimeo\.com/embed/([0-9]+).*$",
            ],
            "https://player.vimeo.com/video/{id}",
        ),
    ]

    def run(self, lines):
        new_lines = []
        for line in lines:
            stripped = line.strip()
            embed = self._match_embed(stripped)
            new_lines.append(embed if embed else line)
        return new_lines

    def _match_embed(self, line: str) -> str | None:
        for _platform, patterns, url_template in self.PATTERNS:
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    return self._embed_html(url_template.format(id=match.group(1)))
        return None

    @staticmethod
    def _embed_html(src: str) -> str:
        return (
            f'<div class="video-embed">'
            f'<iframe src="{src}" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
            f'gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe>'
            f"</div>"
        )


class VideoEmbedExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(VideoEmbedPreprocessor(md), "video_embed", 175)
