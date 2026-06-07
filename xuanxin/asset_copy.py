"""Copy local image assets referenced in Markdown/HTML into build output."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

_MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_HTML_SRC_RE = re.compile(r"""src=["']([^"']+)["']""")
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def is_local_asset(path: str) -> bool:
    """Return True for relative filesystem paths, not URLs or anchors."""
    path = path.strip()
    if not path or path.startswith("#"):
        return False
    return _SCHEME_RE.match(path) is None


def _normalize_asset_ref(path: str) -> str:
    """Strip optional title/attributes suffix from markdown link targets."""
    return path.strip().split()[0]


def collect_asset_paths(*texts: str) -> set[str]:
    """Collect local asset paths from markdown and HTML fragments."""
    paths: set[str] = set()
    for text in texts:
        for pattern in (_MD_IMAGE_RE, _HTML_SRC_RE):
            for match in pattern.finditer(text):
                ref = _normalize_asset_ref(match.group(1))
                if is_local_asset(ref):
                    paths.add(ref)
    return paths


def _safe_source_path(source_root: Path, rel_path: str) -> Path | None:
    rel_path = rel_path.lstrip("/").replace("\\", "/")
    if not rel_path or ".." in Path(rel_path).parts:
        return None
    source_root = source_root.resolve()
    src = (source_root / rel_path).resolve()
    try:
        src.relative_to(source_root)
    except ValueError:
        return None
    return src if src.is_file() else None


def copy_assets(
    paths: set[str] | list[str],
    *,
    source_root: Path,
    output_root: Path,
) -> list[str]:
    """Copy local asset files into output_root, preserving relative paths."""
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    copied: list[str] = []

    for rel in sorted(set(paths)):
        src = _safe_source_path(source_root, rel)
        if src is None:
            continue
        dst = output_root / src.relative_to(source_root)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(str(dst))

    return copied


def copy_asset_tree(
    source_dir: Path,
    *,
    source_root: Path,
    output_root: Path,
) -> list[str]:
    """Copy a directory tree when it lives under source_root."""
    source_dir = source_dir.resolve()
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    try:
        rel = source_dir.relative_to(source_root)
    except ValueError:
        return []
    if not source_dir.is_dir():
        return []

    dst_dir = output_root / rel
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for src in source_dir.rglob("*"):
        if not src.is_file():
            continue
        target = dst_dir / src.relative_to(source_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        copied.append(str(target))
    return copied
