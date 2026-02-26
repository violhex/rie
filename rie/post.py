from __future__ import annotations

import logging

import requests

from .validate import is_safe_image_url

log = logging.getLogger(__name__)


def fetch_post_data(session: requests.Session, post_url: str, timeout: int) -> dict:
    url = post_url + ".json"
    log.debug("Fetching %s", url)

    try:
        resp = session.get(url, timeout=(timeout, timeout), allow_redirects=True)
    except requests.RequestException as exc:
        raise RuntimeError(f"Network error fetching post JSON: {exc}") from exc

    if resp.status_code == 404:
        raise RuntimeError("Post not found (404); it may have been deleted.")
    if resp.status_code == 403:
        raise RuntimeError("Access denied (403); post may be private or quarantined.")
    if resp.status_code == 429:
        raise RuntimeError("Rate-limited (429); try again later or increase --delay.")
    if resp.status_code != 200:
        raise RuntimeError(f"Unexpected HTTP {resp.status_code} from Reddit JSON endpoint.")

    try:
        envelope = resp.json()
    except ValueError as exc:
        raise RuntimeError(f"Reddit response is not valid JSON: {exc}") from exc

    try:
        return envelope[0]["data"]["children"][0]["data"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected JSON structure: {exc}") from exc


def extract_image_urls(post_data: dict) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []

    def add(url: str) -> None:
        url = url.replace("&amp;", "&")
        if url and url not in seen and is_safe_image_url(url):
            seen.add(url)
            urls.append(url)

    media_metadata: dict = post_data.get("media_metadata") or {}
    gallery_data: dict = post_data.get("gallery_data") or {}

    if media_metadata:
        ordered_ids: list[str] = [
            item["media_id"]
            for item in gallery_data.get("items", [])
            if "media_id" in item
        ] or list(media_metadata.keys())

        for media_id in ordered_ids:
            meta = media_metadata.get(media_id)
            if not meta or meta.get("status") != "valid":
                continue
            url = _best_url_from_meta(meta)
            if url:
                add(url)
    else:
        direct = post_data.get("url", "")
        if is_safe_image_url(direct):
            add(direct)
        else:
            for img_entry in (post_data.get("preview") or {}).get("images", []):
                src = img_entry.get("source", {}).get("url", "")
                add(src)

    return urls


def _best_url_from_meta(meta: dict) -> str | None:
    source = meta.get("s") or {}
    url = source.get("u") or source.get("gif")
    if url:
        return url
    previews: list[dict] = meta.get("p") or []
    if not previews:
        return None
    best = max(previews, key=lambda p: p.get("x", 0) * p.get("y", 0))
    return best.get("u")
