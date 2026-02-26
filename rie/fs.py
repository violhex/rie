from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

IMAGE_EXT_FROM_SUFFIX: dict[str, str] = {
    ".jpg": ".jpg",
    ".jpeg": ".jpg",
    ".png": ".png",
    ".gif": ".gif",
    ".webp": ".webp",
    ".avif": ".avif",
}


def ensure_output_dir(path_str: str) -> Path:
    p = Path(path_str).resolve()
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(f"Cannot create output directory {p}: {exc}") from exc
    if not p.is_dir():
        raise RuntimeError(f"{p} exists but is not a directory")
    return p


def image_extension(file_path: Path, fallback_url: str) -> str:
    try:
        header = file_path.read_bytes()[:12]
    except OSError:
        header = b""

    if header:
        if header[:3] == b"\xff\xd8\xff":
            return ".jpg"
        if header[:8] == b"\x89PNG\r\n\x1a\n":
            return ".png"
        if header[:6] in (b"GIF89a", b"GIF87a"):
            return ".gif"
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return ".webp"

    suffix = Path(urlparse(fallback_url).path).suffix.lower()
    return IMAGE_EXT_FROM_SUFFIX.get(suffix, ".jpg")
