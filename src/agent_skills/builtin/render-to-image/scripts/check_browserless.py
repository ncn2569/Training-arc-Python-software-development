#!/usr/bin/env python3
"""Verify Browserless by rendering a minimal PNG through /screenshot."""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BROWSERLESS_URL = "http://localhost:3001"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def resolve_browserless_url(explicit_url: str | None) -> str:
    return (
        explicit_url or os.environ.get("BROWSERLESS_URL") or DEFAULT_BROWSERLESS_URL
    ).rstrip("/")


def check_browserless(browserless_url: str, timeout_seconds: float) -> int:
    payload = {
        "html": "<!doctype html><html><body>browserless-ready</body></html>",
        "options": {"fullPage": True, "type": "png"},
    }
    request = Request(
        f"{browserless_url}/screenshot",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "image/png"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            content_type = response.headers.get_content_type()
            image = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"Browserless returned HTTP {exc.code}{suffix}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            f"Could not reach Browserless at {browserless_url}: {exc}"
        ) from exc

    if content_type != "image/png":
        raise RuntimeError(
            f"Browserless returned {content_type!r}, expected 'image/png'"
        )
    if not image.startswith(PNG_SIGNATURE):
        raise RuntimeError("Browserless returned an empty or invalid PNG image")
    return len(image)


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that Browserless can render through its /screenshot endpoint."
    )
    parser.add_argument(
        "--browserless-url",
        help="Browserless base URL; overrides BROWSERLESS_URL (default: http://localhost:3001)",
    )
    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=10.0,
        help="Request timeout in seconds (default: 10)",
    )
    args = parser.parse_args()
    browserless_url = resolve_browserless_url(args.browserless_url)

    try:
        image_bytes = check_browserless(browserless_url, args.timeout)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"browserless ok url={browserless_url} format=png bytes={image_bytes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
