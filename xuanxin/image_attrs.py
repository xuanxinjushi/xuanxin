"""Parse bubble-style image attributes and render HTML/CSS (see math4ai/docs/markdown_syntax_extensions.md)."""

from __future__ import annotations

import html
import re
from typing import Any

# ![alt](path){width=75% alpha=0.8 .block}
IMAGE_MARKDOWN_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)"
    r"(?:\s*\{(?P<attrs>[^}]*)\})?"
)

# HTML <img ...> emitted by Python-Markdown attr_list
IMG_TAG_RE = re.compile(r"<img\b([^>]*)/?>", re.IGNORECASE)
ATTR_RE = re.compile(
    r'(\w[\w-]*)\s*=\s*"([^"]*)"|class\s*=\s*"([^"]*)"'
)


def parse_attr_block(raw: str | None) -> tuple[list[str], dict[str, str]]:
    """Parse `{.block width=75% alpha=0.8}` into classes and key/value attrs."""
    classes: list[str] = []
    attrs: dict[str, str] = {}
    if not raw:
        return classes, attrs

    for token in raw.split():
        if token.startswith("."):
            cls = token[1:].strip()
            if cls:
                classes.append(cls)
        elif "=" in token:
            key, _, value = token.partition("=")
            key = key.strip()
            value = value.strip()
            if key:
                attrs[key] = value
    return classes, attrs


def inject_tp_image_class(line: str) -> str:
    """Add `.tp-image` to the attribute block on a markdown image line."""
    match = IMAGE_MARKDOWN_RE.search(line)
    if not match:
        return line.rstrip() + "{.tp-image}"

    alt = match.group("alt")
    src = match.group("src")
    attrs = match.group("attrs")
    if attrs is None:
        new_attrs = ".tp-image"
    else:
        new_attrs = f".tp-image {attrs}".strip()
    replacement = f"![{alt}]({src}){{{new_attrs}}}"
    return IMAGE_MARKDOWN_RE.sub(replacement, line, count=1)


def _parse_html_attrs(tag_inner: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for match in ATTR_RE.finditer(tag_inner):
        if match.group(3) is not None:
            parsed["class"] = match.group(3)
        else:
            parsed[match.group(1)] = match.group(2)
    return parsed


def _style_fragment(styles: list[str]) -> str:
    return "; ".join(s for s in styles if s) + (";" if styles else "")


def _resolve_bottom_offset(attrs: dict[str, str]) -> str:
    raw = (
        attrs.pop("bottom-offset", None)
        or attrs.pop("bottom", None)
        or attrs.pop("bottom-distance", None)
        or attrs.pop("yshift", None)
    )
    return raw if raw else "0"


def _build_styles(attrs: dict[str, str], classes: set[str]) -> list[str]:
    styles: list[str] = []

    width = attrs.pop("width", None)
    height = attrs.pop("height", None)
    alpha = attrs.pop("alpha", None) or attrs.pop("opacity", None)
    align = attrs.pop("align", None) or attrs.pop("alignment", None)
    rotate = attrs.pop("rotate", None) or attrs.pop("angle", None)

    is_background = "background" in classes
    is_fullpage = "fullpage" in classes
    is_bottom_right = "bottom-right" in classes
    bottom_offset = _resolve_bottom_offset(attrs) if is_background and is_bottom_right else "0"

    if width and not is_background:
        styles.append(f"width: {width}")
        styles.append("max-width: 100%")
        if not height:
            styles.append("height: auto")
    if height and not is_background:
        styles.append(f"height: {height}")
        if not width:
            styles.append("width: auto")

    if alpha is not None and not is_background:
        try:
            num = float(alpha)
            if 0 <= num <= 1:
                styles.append(f"opacity: {num}")
        except ValueError:
            pass

    if rotate is not None:
        try:
            styles.append(f"transform: rotate({float(rotate)}deg)")
        except ValueError:
            pass

    if align == "center":
        styles.append("display: block")
        styles.append("margin-left: auto")
        styles.append("margin-right: auto")
    elif align == "right":
        styles.append("display: block")
        styles.append("margin-left: auto")
        styles.append("margin-right: 0")
    elif align == "left":
        styles.append("display: block")
        styles.append("margin-right: auto")

    if is_background:
        op = alpha
        try:
            opacity = float(op) if op is not None else 0.35
        except ValueError:
            opacity = 0.35
        opacity = min(1.0, max(0.0, opacity))
        styles.extend(
            [
                "pointer-events: none",
                f"opacity: {opacity}",
                "box-sizing: border-box",
                "z-index: 0",
            ]
        )
        if is_bottom_right:
            tw = width or "60%"
            styles.extend(
                [
                    "position: absolute",
                    "right: 0",
                    f"bottom: {bottom_offset}",
                    f"width: {tw}",
                    "max-width: 100%",
                    "height: auto",
                ]
            )
        else:
            styles.extend(
                [
                    "position: fixed",
                    "left: 0",
                    "top: 0",
                    "width: 100vw",
                    "height: 100vh",
                    "max-width: none",
                    "object-fit: cover",
                ]
            )
    elif is_fullpage:
        fw = width or "100%"
        fh = height or "auto"
        styles.extend(
            [
                f"width: {fw}",
                f"height: {fh}",
                "max-width: 100%",
                "object-fit: contain",
            ]
        )

    return styles


def _render_img_tag(src: str, alt: str, classes: list[str], style: str) -> str:
    class_attr = f' class="{html.escape(" ".join(classes))}"' if classes else ""
    style_attr = f' style="{html.escape(style)}"' if style else ""
    alt_attr = f' alt="{html.escape(alt)}"' if alt else ' alt=""'
    return f'<img src="{html.escape(src)}"{alt_attr}{class_attr}{style_attr} />'


def transform_img_tag(full_tag: str, tag_inner: str) -> str:
    attrs = _parse_html_attrs(tag_inner)
    src = attrs.get("src", "")
    alt = attrs.get("alt", "")

    classes = attrs.get("class", "").split()
    class_set = set(classes)

    styles = _build_styles(dict(attrs), class_set)
    style = _style_fragment(styles)

    # Drop attrs that become CSS or wrappers; keep src/alt only on <img>.
    for key in (
        "width",
        "height",
        "alpha",
        "opacity",
        "align",
        "alignment",
        "rotate",
        "angle",
        "block",
        "inline",
        "wrap",
        "fullpage",
        "background",
        "bottom-offset",
        "bottom",
        "bottom-distance",
        "yshift",
    ):
        attrs.pop(key, None)

    img_html = _render_img_tag(src, alt, classes, style)

    if "fullpage" in class_set:
        return f'<div class="fullpage-image">{img_html}</div>'

    if "block" in class_set and alt:
        caption = html.escape(alt)
        fig_classes = "image-block"
        if "caption-text-only" in class_set:
            fig_classes += " caption-text-only"
        return (
            f'<figure class="{fig_classes}">{img_html}'
            f"<figcaption>{caption}</figcaption></figure>"
        )

    if "wrap" in class_set:
        align = "right"
        for cls in classes:
            if cls.startswith("align-"):
                align = cls.split("-", 1)[1]
        float_dir = "left" if "left" in align else "right"
        margin = "0 1.25rem 1rem 0" if float_dir == "left" else "0 0 1rem 1.25rem"
        wrapped_style = _style_fragment(styles + [f"float: {float_dir}", f"margin: {margin}"])
        return _render_img_tag(src, alt, [c for c in classes if not c.startswith("align-")], wrapped_style)

    if "inline" in class_set:
        wrapped_style = _style_fragment(styles + ["display: inline", "vertical-align: middle"])
        return _render_img_tag(src, alt, classes, wrapped_style)

    return img_html


BG_IMG_IN_P_RE = re.compile(
    r'<p>\s*(<img\b[^>]*\bclass="[^"]*\bbackground\b[^"]*"[^>]*/>)\s*</p>',
    re.IGNORECASE,
)
H2_SECTION_RE = re.compile(
    r"(<h2\b[^>]*>.*?</h2>)(.*?)(?=<h2\b|$)",
    re.IGNORECASE | re.DOTALL,
)


def _wrap_background_section(heading: str, body: str) -> str:
    if not BG_IMG_IN_P_RE.search(body):
        return heading + body

    out = [heading]
    pos = 0
    for bg in BG_IMG_IN_P_RE.finditer(body):
        out.append(body[pos : bg.start()])
        img_tag = bg.group(1)
        pos = bg.end()
        next_bg = BG_IMG_IN_P_RE.search(body, pos)
        inner_end = next_bg.start() if next_bg else len(body)
        inner = body[pos:inner_end]
        out.append(f'<div class="image-background-section">{img_tag}{inner}</div>')
        pos = inner_end
    out.append(body[pos:])
    return "".join(out)


def _wrap_orphan_background_blocks(html: str) -> str:
    """Wrap background images that appear outside an h2 section."""
    first_h2 = html.find("<h2")
    if first_h2 == -1:
        bg = BG_IMG_IN_P_RE.search(html)
        if not bg:
            return html
        img_tag = bg.group(1)
        before = html[: bg.start()]
        after = html[bg.end() :]
        return f'{before}<div class="image-background-section">{img_tag}{after}</div>'

    pre_h2 = html[:first_h2]
    bg = BG_IMG_IN_P_RE.search(pre_h2)
    if not bg or "image-background-section" in pre_h2:
        return html

    img_tag = bg.group(1)
    before = pre_h2[: bg.start()]
    after = pre_h2[bg.end() :]
    wrapped_pre = f'{before}<div class="image-background-section">{img_tag}{after}</div>'
    return wrapped_pre + html[first_h2:]


def wrap_tp_image_section(html: str) -> str:
    """Chapter opening **tp_image** — bottom-right in its block (like bubble title-page art)."""
    with_quote = re.compile(
        r"(<blockquote>.*?</blockquote>\s*)<p>\s*(<img\b[^>]*\btp-image\b[^>]*/>)\s*</p>",
        re.IGNORECASE | re.DOTALL,
    )
    html = with_quote.sub(r'<div class="tp-image-section">\1\2</div>', html, count=1)

    alone = re.compile(
        r'<p>\s*(<img\b[^>]*\btp-image\b[^>]*/>)\s*</p>',
        re.IGNORECASE,
    )
    return alone.sub(r'<div class="tp-image-section">\1</div>', html)


def wrap_background_sections(html: str) -> str:
    """Place section background images in a relative container (not viewport-fixed)."""
    html = H2_SECTION_RE.sub(
        lambda m: _wrap_background_section(m.group(1), m.group(2)),
        html,
    )
    return _wrap_orphan_background_blocks(html)


def postprocess_image_html(html: str) -> str:
    html = IMG_TAG_RE.sub(lambda m: transform_img_tag(m.group(0), m.group(1)), html)
    html = wrap_tp_image_section(html)
    return wrap_background_sections(html)
