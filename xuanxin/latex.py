"""Protect LaTeX math from Markdown processing."""

from __future__ import annotations

import re


def protect_latex(content: str) -> tuple[str, list[dict[str, str]]]:
    """Replace LaTeX blocks with placeholders before Markdown conversion."""
    latex_placeholders: list[dict[str, str]] = []
    processed = content

    def replace_display(match: re.Match[str]) -> str:
        latex = match.group(1)
        placeholder = f"<LATEX_DISPLAY_{len(latex_placeholders)}>"
        latex_placeholders.append({"placeholder": placeholder, "content": f"$${latex}$$"})
        return placeholder

    processed = re.sub(r"\$\$([\s\S]*?)\$\$", replace_display, processed)

    def replace_inline(match: re.Match[str]) -> str:
        latex = match.group(1)
        placeholder = f"<LATEX_INLINE_{len(latex_placeholders)}>"
        latex_placeholders.append({"placeholder": placeholder, "content": f"${latex}$"})
        return placeholder

    processed = re.sub(r"\$([^$\n]+?)\$", replace_inline, processed)
    return processed, latex_placeholders


def restore_latex(html_content: str, latex_placeholders: list[dict[str, str]]) -> str:
    """Restore LaTeX placeholders after Markdown conversion."""
    for item in sorted(latex_placeholders, key=lambda x: len(x["placeholder"]), reverse=True):
        html_content = html_content.replace(item["placeholder"], item["content"])
    return html_content
