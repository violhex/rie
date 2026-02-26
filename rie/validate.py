from __future__ import annotations

from urllib.parse import urlparse, urlunparse

ALLOWED_REDDIT_HOSTS: frozenset[str] = frozenset(
    {"reddit.com", "www.reddit.com", "old.reddit.com", "redd.it"}
)

ALLOWED_IMAGE_HOSTS: frozenset[str] = frozenset(
    {"i.redd.it", "preview.redd.it", "external-preview.redd.it", "i.imgur.com"}
)


def validate_reddit_url(raw: str) -> str:
    parsed = urlparse(raw)

    if parsed.scheme != "https":
        raise ValueError(f"Only https:// URLs accepted; got scheme={parsed.scheme!r}")

    if parsed.username or parsed.password:
        raise ValueError("URL must not contain credentials")

    host = parsed.netloc.lower().rstrip(".")
    if host not in ALLOWED_REDDIT_HOSTS:
        raise ValueError(f"Host {host!r} is not an allowed Reddit domain")

    if "/comments/" not in parsed.path:
        raise ValueError("URL does not look like a Reddit post (missing /comments/)")

    return urlunparse(("https", host, parsed.path.rstrip("/"), "", "", ""))


def is_safe_image_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme != "https":
        return False
    host = parsed.netloc.lower().rstrip(".")
    return host in ALLOWED_IMAGE_HOSTS
