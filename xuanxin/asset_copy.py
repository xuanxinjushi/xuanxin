"""Copy local image assets referenced in Markdown/HTML into build output."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from xuanxin.gallery_crypto import encrypt_file, encrypted_asset_path
from xuanxin.image_convert import (
    DEFAULT_PNG_TO_JPG_THRESHOLD,
    converted_png_jpg_path,
    ensure_converted_png_jpg,
    should_convert_png,
)

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


def rewrite_asset_paths(text: str, rewrites: dict[str, str]) -> str:
    """Replace copied asset paths with optimized output paths."""
    if not rewrites:
        return text
    updated = text
    for old, new in sorted(rewrites.items(), key=lambda item: len(item[0]), reverse=True):
        updated = updated.replace(old, new)
    return updated


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


def _publish_file(
    src: Path,
    dst: Path,
    *,
    source_root: Path,
    output_root: Path,
    png_threshold: int | None,
    encrypt_password: str | None = None,
) -> tuple[Path, dict[str, str]]:
    """Copy or convert one asset file into the output tree."""
    rewrites: dict[str, str] = {}
    dst.parent.mkdir(parents=True, exist_ok=True)
    rel_src = src.relative_to(source_root).as_posix()
    publish_src = src
    publish_dst = dst

    if png_threshold is not None and should_convert_png(src, png_threshold):
        src_jpg = ensure_converted_png_jpg(src, threshold=png_threshold)
        assert src_jpg is not None
        publish_src = src_jpg
        publish_dst = converted_png_jpg_path(dst)
        rewrites[rel_src] = publish_dst.relative_to(output_root).as_posix()

    publish_dst.parent.mkdir(parents=True, exist_ok=True)

    if encrypt_password:
        enc_dst = encrypted_asset_path(publish_dst)
        encrypt_file(publish_src, enc_dst, encrypt_password)
        optimized_rel = publish_dst.relative_to(output_root).as_posix()
        if optimized_rel != rel_src:
            rewrites[rel_src] = optimized_rel
        return enc_dst, rewrites

    shutil.copy2(publish_src, publish_dst)
    final_rel = publish_dst.relative_to(output_root).as_posix()
    if final_rel != rel_src:
        rewrites[rel_src] = final_rel
    return publish_dst, rewrites


def copy_assets(
    paths: set[str] | list[str],
    *,
    source_root: Path,
    output_root: Path,
    png_to_jpg_threshold: int | None = DEFAULT_PNG_TO_JPG_THRESHOLD,
    encrypt_paths: dict[str, str] | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Copy local asset files into output_root, preserving relative paths."""
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    copied: list[str] = []
    rewrites: dict[str, str] = {}

    encrypt_paths = encrypt_paths or {}

    for rel in sorted(set(paths)):
        src = _safe_source_path(source_root, rel)
        if src is None:
            continue
        dst = output_root / src.relative_to(source_root)
        out_path, file_rewrites = _publish_file(
            src,
            dst,
            source_root=source_root,
            output_root=output_root,
            png_threshold=png_to_jpg_threshold,
            encrypt_password=encrypt_paths.get(rel),
        )
        copied.append(str(out_path))
        rewrites.update(file_rewrites)

    return copied, rewrites


def copy_asset_tree(
    source_dir: Path,
    *,
    source_root: Path,
    output_root: Path,
    png_to_jpg_threshold: int | None = DEFAULT_PNG_TO_JPG_THRESHOLD,
    encrypt_paths: dict[str, str] | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Copy a directory tree when it lives under source_root."""
    source_dir = source_dir.resolve()
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    try:
        rel = source_dir.relative_to(source_root)
    except ValueError:
        return [], {}
    if not source_dir.is_dir():
        return [], {}

    copied: list[str] = []
    rewrites: dict[str, str] = {}
    encrypt_paths = encrypt_paths or {}
    for src in source_dir.rglob("*"):
        if not src.is_file():
            continue
        rel_path = (rel / src.relative_to(source_dir)).as_posix()
        dst = output_root / rel / src.relative_to(source_dir)
        out_path, file_rewrites = _publish_file(
            src,
            dst,
            source_root=source_root,
            output_root=output_root,
            png_threshold=png_to_jpg_threshold,
            encrypt_password=encrypt_paths.get(rel_path),
        )
        copied.append(str(out_path))
        rewrites.update(file_rewrites)

    return copied, rewrites
