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

    if width and not is_background and not is_fullpage:
        styles.append(f"width: {width}")
        styles.append("max-width: 100%")
        if not height:
            styles.append("height: auto")
    if height and not is_background and not is_fullpage:
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
            # Scoped to `.image-background-section` (not viewport-fixed).
            fw = width or "100%"
            fh = height or "100%"
            styles.extend(
                [
                    "position: absolute",
                    "left: 0",
                    "top: 0",
                    f"width: {fw}",
                    f"height: {fh}",
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
PAGE_BREAK_MARKER = '<div class="xuanxin-pagebreak"'
SECTION_BOUNDARY_RE = r"(?=<h[12]\b|<div class=\"xuanxin-pagebreak\"|$)"
H2_SECTION_RE = re.compile(
    rf"(<h2\b[^>]*>.*?</h2>)(.*?){SECTION_BOUNDARY_RE}",
    re.IGNORECASE | re.DOTALL,
)
H1_SECTION_RE = re.compile(
    rf"(<h1\b[^>]*>.*?</h1>)(.*?){SECTION_BOUNDARY_RE}",
    re.IGNORECASE | re.DOTALL,
)


def _next_wrap_boundary(html: str, pos: int) -> int:
    """Stop background inner content at the next bg image or page break."""
    candidates = [len(html)]
    next_bg = BG_IMG_IN_P_RE.search(html, pos)
    if next_bg:
        candidates.append(next_bg.start())
    next_pb = html.find(PAGE_BREAK_MARKER, pos)
    if next_pb != -1:
        candidates.append(next_pb)
    return min(candidates)


def _is_bottom_right_bg(img_tag: str) -> bool:
    return "bottom-right" in img_tag.lower()


def _split_section_img_inner(section_html: str) -> tuple[str, str]:
    match = re.match(
        r'<div class="image-background-section">(<img\b[^>]*/>)(.*)</div>\s*$',
        section_html,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return "", section_html
    return match.group(1), match.group(2)


_INNER_BLOCK_RE = re.compile(
    r"<(?:p|div|h[1-6]|blockquote)\b[^>]*>.*?</(?:p|div|h[1-6]|blockquote)>"
    r'|<div class="xuanxin-blank"[^>]*/>',
    re.DOTALL | re.IGNORECASE,
)


def _split_inner_blocks(inner: str) -> list[str]:
    if not inner.strip():
        return []
    blocks = _INNER_BLOCK_RE.findall(inner)
    return blocks if blocks else [inner]


def _distribute_blocks(blocks: list[str], count: int) -> list[str]:
    inners = [""] * count
    total = len(blocks)
    for index, block in enumerate(blocks):
        section = (index * count) // total
        if section >= count:
            section = count - 1
        inners[section] += block
    return inners


def _rebalance_stack_sections(run: list[str]) -> list[str]:
    """Spread body text across stack bands when only the first section has content."""
    parsed = [_split_section_img_inner(section) for section in run]
    if len(parsed) < 2:
        return run

    if any(_split_inner_blocks(inner) for _, inner in parsed[1:]):
        return run

    all_blocks: list[str] = []
    for _, inner in parsed:
        all_blocks.extend(_split_inner_blocks(inner))
    if len(all_blocks) < 2:
        return run

    distributed = _distribute_blocks(all_blocks, len(parsed))
    rebuilt: list[str] = []
    for (img_tag, _), inner in zip(parsed, distributed):
        rebuilt.append(f'<div class="image-background-section">{img_tag}{inner}</div>')
    return rebuilt


def _mark_stack_item(section_html: str) -> str:
    section_html = section_html.replace(
        'class="image-background-section"',
        'class="image-background-section image-background-stack-item"',
        1,
    )
    section_html = re.sub(
        r'(<img\b[^>]*\bclass="[^"]*\bbackground\b[^"]*"[^>]*\sstyle=")([^"]*)(")',
        lambda m: m.group(1)
        + re.sub(r"\s*(?:width|height):\s*[^;\"]+;?", "", m.group(2))
        + m.group(3),
        section_html,
        count=1,
        flags=re.IGNORECASE,
    )
    return section_html


def _stack_wrap_sections(sections: list[str], is_full_bleed: list[bool]) -> list[str]:
    """Group consecutive full-bleed backgrounds into equal vertical slices (2+)."""
    wrapped: list[str] = []
    index = 0
    while index < len(sections):
        if not is_full_bleed[index]:
            wrapped.append(sections[index])
            index += 1
            continue

        run_start = index
        while index < len(sections) and is_full_bleed[index]:
            index += 1
        run = sections[run_start:index]

        if len(run) >= 2:
            run = _rebalance_stack_sections(run)
            count = len(run)
            items = [_mark_stack_item(section_html) for section_html in run]
            wrapped.append(
                f'<div class="image-background-stack" data-bg-count="{count}" '
                f'style="--bg-stack-count: {count};">'
                + "".join(items)
                + "</div>"
            )
        else:
            wrapped.extend(run)
    return wrapped


def _wrap_background_section(heading: str, body: str) -> str:
    if not BG_IMG_IN_P_RE.search(body):
        return heading + body

    gaps: list[str] = []
    sections: list[str] = []
    is_full_bleed: list[bool] = []
    pos = 0
    for bg in BG_IMG_IN_P_RE.finditer(body):
        gap_before = body[pos : bg.start()]
        img_tag = bg.group(1)
        pos = bg.end()
        inner_end = _next_wrap_boundary(body, pos)
        inner = body[pos:inner_end]
        pos = inner_end

        if _is_bottom_right_bg(img_tag):
            sections.append(
                '<div class="image-background-section image-background-bottom-right">'
                f"{gap_before}{img_tag}{inner}</div>"
            )
            is_full_bleed.append(False)
            gaps.append("")
        else:
            gaps.append(gap_before)
            sections.append(f'<div class="image-background-section">{img_tag}{inner}</div>')
            is_full_bleed.append(True)

    gaps.append(body[pos:])

    sections = _stack_wrap_sections(sections, is_full_bleed)

    out = [heading]
    for index, section_html in enumerate(sections):
        out.append(gaps[index])
        out.append(section_html)
    out.append(gaps[-1])
    return "".join(out)


def _wrap_orphan_background_blocks(html: str) -> str:
    """Wrap background images that appear outside a heading section."""
    first_heading = html.find("<h1")
    if first_heading == -1:
        first_heading = html.find("<h2")
    if first_heading == -1:
        bg = BG_IMG_IN_P_RE.search(html)
        if not bg:
            return html
        img_tag = bg.group(1)
        before = html[: bg.start()]
        after_end = _next_wrap_boundary(html, bg.end())
        after = html[bg.end() : after_end]
        rest = html[after_end:]
        return (
            f'{before}<div class="image-background-section">{img_tag}{after}</div>{rest}'
        )

    pre_heading = html[:first_heading]
    bg = BG_IMG_IN_P_RE.search(pre_heading)
    if not bg or "image-background-section" in pre_heading:
        return html

    img_tag = bg.group(1)
    before = pre_heading[: bg.start()]
    after_end = _next_wrap_boundary(pre_heading, bg.end())
    after = pre_heading[bg.end() : after_end]
    wrapped_pre = f'{before}<div class="image-background-section">{img_tag}{after}</div>'
    return wrapped_pre + pre_heading[after_end:] + html[first_heading:]


def wrap_background_sections(html: str) -> str:
    """Place section background images in a relative container (not viewport-fixed)."""
    html = H2_SECTION_RE.sub(
        lambda m: _wrap_background_section(m.group(1), m.group(2)),
        html,
    )
    html = H1_SECTION_RE.sub(
        lambda m: _wrap_background_section(m.group(1), m.group(2)),
        html,
    )
    return _wrap_orphan_background_blocks(html)


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


def unwrap_fullpage_blocks(html: str) -> str:
    """Markdown wraps block-level fullpage divs in ``<p>`` — unwrap for valid HTML/DOM."""
    fullpage_in_p = re.compile(
        r'<p>\s*(<div class="fullpage-image">.*?</div>)\s*</p>',
        re.IGNORECASE | re.DOTALL,
    )
    return fullpage_in_p.sub(r"\1", html)


def postprocess_image_html(html: str) -> str:
    html = IMG_TAG_RE.sub(lambda m: transform_img_tag(m.group(0), m.group(1)), html)
    html = wrap_tp_image_section(html)
    html = wrap_background_sections(html)
    return unwrap_fullpage_blocks(html)
