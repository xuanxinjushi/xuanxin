"""Convert large PNG assets to JPEG during static site builds."""

from __future__ import annotations

from pathlib import Path

DEFAULT_PNG_TO_JPG_THRESHOLD = 100 * 1024
DEFAULT_JPEG_QUALITY = 85


def converted_png_jpg_path(path: Path) -> Path:
    """Return the JPEG path used for an optimized PNG asset."""
    return path.with_name(f"{path.stem}_small.jpg")


def should_convert_png(path: Path, threshold: int = DEFAULT_PNG_TO_JPG_THRESHOLD) -> bool:
    """Return True when a PNG should be converted to JPEG."""
    return path.suffix.lower() == ".png" and path.is_file() and path.stat().st_size > threshold


def convert_png_to_jpg(
    src: Path,
    dst: Path,
    *,
    quality: int = DEFAULT_JPEG_QUALITY,
) -> None:
    """Write a JPEG version of a PNG file."""
    from PIL import Image

    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as image:
        if image.mode in ("RGBA", "LA") or (
            image.mode == "P" and "transparency" in image.info
        ):
            background = Image.new("RGB", image.size, (255, 255, 255))
            rgba = image.convert("RGBA")
            background.paste(rgba, mask=rgba.split()[-1])
            rgb = background
        else:
            rgb = image.convert("RGB")
        rgb.save(dst, format="JPEG", quality=quality, optimize=True)


def ensure_converted_png_jpg(
    png_path: Path,
    *,
    threshold: int | None = DEFAULT_PNG_TO_JPG_THRESHOLD,
) -> Path | None:
    """Create or refresh ``{stem}_small.jpg`` beside a large PNG in place."""
    if threshold is None or not should_convert_png(png_path, threshold):
        return None
    jpg_path = converted_png_jpg_path(png_path)
    if jpg_path.exists() and jpg_path.stat().st_mtime >= png_path.stat().st_mtime:
        return jpg_path
    convert_png_to_jpg(png_path, jpg_path)
    return jpg_path
