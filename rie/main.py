from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from .download import download_image
from .fs import ensure_output_dir, image_extension
from .http import build_session
from .post import extract_image_urls, fetch_post_data
from .validate import validate_reddit_url

DEFAULT_DELAY_MS: int = 1000
DEFAULT_TIMEOUT_S: int = 15
DEFAULT_MAX_BYTES: int = 25 * 1024 * 1024

log = logging.getLogger(__name__)


def run_downloads(
    session,
    urls: list[str],
    output_dir: Path,
    max_images: int | None,
    delay_ms: int,
    timeout: int,
    max_bytes: int,
) -> tuple[int, int, int]:
    downloaded = 0
    skipped = 0
    errors = 0
    seen_hashes: set[str] = set()
    delay_s = delay_ms / 1000.0

    candidates = urls if max_images is None else urls[:max_images]
    total = len(candidates)

    for idx, url in enumerate(candidates, start=1):
        if idx > 1:
            time.sleep(delay_s)

        tmp = output_dir / f".tmp_{idx:04d}"
        digest = download_image(session, url, tmp, timeout, max_bytes)

        if digest is None:
            errors += 1
            continue

        if digest in seen_hashes:
            log.info("Skipping duplicate content at index %d", idx)
            tmp.unlink(missing_ok=True)
            skipped += 1
            continue

        seen_hashes.add(digest)
        ext = image_extension(tmp, url)
        final = output_dir / f"image_{idx:04d}{ext}"

        try:
            tmp.rename(final)
        except OSError as exc:
            log.error("Rename failed %s → %s: %s", tmp, final, exc)
            tmp.unlink(missing_ok=True)
            errors += 1
            continue

        log.info("[%d/%d] %s", idx, total, final.name)
        downloaded += 1

    return downloaded, skipped, errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download all images from a Reddit post.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("url", help="Reddit post URL (https only)")
    parser.add_argument("-o", "--output-dir", required=True, help="Directory to save images")
    parser.add_argument("--max-images", type=int, default=None, metavar="N",
                        help="Maximum images to download")
    parser.add_argument("--delay", type=int, default=DEFAULT_DELAY_MS, metavar="MS",
                        help="Milliseconds between requests")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S, metavar="SECONDS",
                        help="HTTP connect+read timeout per request")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, metavar="BYTES",
                        help="Max download size per file in bytes")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    try:
        post_url = validate_reddit_url(args.url)
    except ValueError as exc:
        log.error("Invalid URL: %s", exc)
        return 1

    try:
        output_dir = ensure_output_dir(args.output_dir)
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1

    log.info("Post:   %s", post_url)
    log.info("Output: %s", output_dir)

    session = build_session()

    try:
        post_data = fetch_post_data(session, post_url, args.timeout)
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1

    image_urls = extract_image_urls(post_data)

    if not image_urls:
        log.warning("No images found in post.")
        return 0

    log.info("Found %d image(s)", len(image_urls))

    downloaded, skipped, errors = run_downloads(
        session=session,
        urls=image_urls,
        output_dir=output_dir,
        max_images=args.max_images,
        delay_ms=args.delay,
        timeout=args.timeout,
        max_bytes=args.max_bytes,
    )

    log.info(
        "Done — found: %d | downloaded: %d | skipped: %d | errors: %d",
        len(image_urls), downloaded, skipped, errors,
    )

    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
