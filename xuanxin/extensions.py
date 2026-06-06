"""Markdown extensions: bubble image attributes, tp_image, video embeds."""

from __future__ import annotations

import re

from markdown.extensions import Extension
from markdown.inlinepatterns import IMAGE_LINK_RE, ImageInlineProcessor
from markdown.postprocessors import Postprocessor
from markdown.preprocessors import Preprocessor

from xuanxin.image_attrs import inject_tp_image_class, postprocess_image_html


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


LATEX_PAGEBREAK_RE = re.compile(
    r"^\s*\\(?:newpage|clearpage|cleardoublepage)\s*$"
)

PAGE_BREAK_HTML = '<div class="xuanxin-pagebreak" aria-hidden="true"></div>'

LATEX_FENCE_START_RE = re.compile(r"^```\{=latex\}\s*$")
FENCE_END_RE = re.compile(r"^```\s*$")


class LatexFencedBlockPreprocessor(Preprocessor):
    """Drop Pandoc ``{=latex}`` fenced blocks (PDF-only; bubble markers like END_OF_PREFACE)."""

    def run(self, lines):
        out: list[str] = []
        in_block = False
        for line in lines:
            stripped = line.strip()
            if not in_block:
                if LATEX_FENCE_START_RE.match(stripped):
                    in_block = True
                else:
                    out.append(line)
            elif FENCE_END_RE.match(stripped):
                in_block = False
        return out


class LatexFencedBlockExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(
            LatexFencedBlockPreprocessor(md), "latex_fenced", 26
        )


class LatexPageBreakPreprocessor(Preprocessor):
    """Convert LaTeX page-break lines (``\\newpage``, etc.) to HTML/CSS page breaks."""

    def run(self, lines):
        out: list[str] = []
        for line in lines:
            if LATEX_PAGEBREAK_RE.match(line):
                out.append(PAGE_BREAK_HTML)
            else:
                out.append(line)
        return out


class LatexPageBreakExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(
            LatexPageBreakPreprocessor(md), "latex_pagebreak", 27
        )


class BackslashBlankLinePreprocessor(Preprocessor):
    """Convert a lone ``\\`` line to a visible blank line (bubble: ``\\hfill\\break``)."""

    def run(self, lines):
        out: list[str] = []
        for line in lines:
            if line.strip() == "\\":
                out.append('<div class="xuanxin-blank" aria-hidden="true"></div>')
            else:
                out.append(line)
        return out


class BackslashBlankLineExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(
            BackslashBlankLinePreprocessor(md), "backslash_blank", 28
        )


class TpImagePreprocessor(Preprocessor):
    """Remove **tp_image** marker and tag the following image as `.tp-image`."""

    MARKER = "**tp_image**"

    def run(self, lines):
        out: list[str] = []
        i = 0
        while i < len(lines):
            if lines[i].strip() == self.MARKER:
                i += 1
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    out.append(inject_tp_image_class(lines[i]))
                    i += 1
                continue
            out.append(lines[i])
            i += 1
        return out


class TpImageExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(TpImagePreprocessor(md), "tp_image", 30)


class ImageAttributesPostprocessor(Postprocessor):
    """Map bubble-style image attributes (width, alpha, .background, etc.) to HTML/CSS."""

    def run(self, text):
        return postprocess_image_html(text)


class ImageAttributesExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(
            ImageAttributesPostprocessor(md), "image_attributes", 25
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
