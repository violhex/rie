from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import requests

CHUNK_SIZE = 65536

log = logging.getLogger(__name__)


def download_image(
    session: requests.Session,
    url: str,
    dest: Path,
    timeout: int,
    max_bytes: int,
) -> str | None:
    try:
        resp = session.get(url, timeout=(timeout, timeout), stream=True, allow_redirects=True)
    except requests.RequestException as exc:
        log.warning("Network error fetching %s: %s", url, exc)
        return None

    if resp.status_code != 200:
        log.warning("HTTP %d for %s", resp.status_code, url)
        resp.close()
        return None

    content_type = resp.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        log.warning("Rejected Content-Type %r for %s", content_type, url)
        resp.close()
        return None

    hasher = hashlib.sha256()
    bytes_written = 0

    try:
        with dest.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    log.warning("Size limit exceeded (%d B) for %s; aborting", max_bytes, url)
                    dest.unlink(missing_ok=True)
                    return None
                hasher.update(chunk)
                fh.write(chunk)
    except OSError as exc:
        log.error("Write error to %s: %s", dest, exc)
        dest.unlink(missing_ok=True)
        return None

    log.debug("Wrote %d bytes → %s", bytes_written, dest.name)
    return hasher.hexdigest()
