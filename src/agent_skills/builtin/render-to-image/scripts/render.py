#!/usr/bin/env python3
"""Render a local HTML, HTM, or Mermaid file to a full-page PNG."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from validate_input import validate_input

DEFAULT_BROWSERLESS_URL = "http://localhost:3001"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "mermaid.html"
SOURCE_PLACEHOLDER = "__MERMAID_SOURCE_JSON__"


def resolve_browserless_url(explicit_url: str | None) -> str:
    return (
        explicit_url or os.environ.get("BROWSERLESS_URL") or DEFAULT_BROWSERLESS_URL
    ).rstrip("/")


def build_html(input_path: Path) -> tuple[str, bool]:
    source = input_path.read_text(encoding="utf-8")
    if input_path.suffix.lower() != ".mmd":
        return source, False

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if template.count(SOURCE_PLACEHOLDER) != 1:
        raise ValueError(
            f"Mermaid template must contain exactly one {SOURCE_PLACEHOLDER} placeholder"
        )
    return template.replace(SOURCE_PLACEHOLDER, json.dumps(source)), True


def build_payload(
    html: str,
    *,
    is_mermaid: bool,
    viewport_width: int,
    viewport_height: int,
    device_scale_factor: float,
    timeout_seconds: float,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "html": html,
        "options": {"fullPage": True, "type": "png"},
        "viewport": {
            "width": viewport_width,
            "height": viewport_height,
            "deviceScaleFactor": device_scale_factor,
        },
    }
    if is_mermaid:
        payload["waitForFunction"] = {
            "fn": "() => window.__RENDER_READY__ === true",
            "timeout": int(timeout_seconds * 1000),
        }
    return payload


def request_png(
    browserless_url: str,
    payload: dict[str, object],
    timeout_seconds: float,
) -> bytes:
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
    if not image:
        raise RuntimeError("Browserless returned an empty image")
    if not image.startswith(PNG_SIGNATURE):
        raise RuntimeError("Browserless response does not have a valid PNG signature")
    return image


def write_png(output_path: Path, image: bytes) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
        temporary.write(image)
        temporary_path = Path(temporary.name)
    temporary_path.replace(output_path)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a local HTML, HTM, or Mermaid file to a full-page PNG through Browserless."
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Source .html, .htm, or .mmd file"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Destination .png file"
    )
    parser.add_argument(
        "--browserless-url",
        help="Browserless base URL; overrides BROWSERLESS_URL (default: http://localhost:3001)",
    )
    parser.add_argument(
        "--viewport-width",
        type=positive_int,
        default=1440,
        help="Viewport width in pixels (default: 1440)",
    )
    parser.add_argument(
        "--viewport-height",
        type=positive_int,
        default=900,
        help="Viewport height in pixels (default: 900)",
    )
    parser.add_argument(
        "--device-scale-factor",
        type=positive_float,
        default=1.0,
        help="Device scale factor (default: 1)",
    )
    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=30.0,
        help="Request and Mermaid readiness timeout in seconds (default: 30)",
    )
    args = parser.parse_args()

    try:
        validate_input(args.input)
        if args.output.suffix.lower() != ".png":
            raise ValueError(f"--output must end in .png: {args.output}")
        html, is_mermaid = build_html(args.input)
        payload = build_payload(
            html,
            is_mermaid=is_mermaid,
            viewport_width=args.viewport_width,
            viewport_height=args.viewport_height,
            device_scale_factor=args.device_scale_factor,
            timeout_seconds=args.timeout,
        )
        browserless_url = resolve_browserless_url(args.browserless_url)
        image = request_png(browserless_url, payload, args.timeout)
        write_png(args.output, image)
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"rendered format=png bytes={len(image)} output={args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
