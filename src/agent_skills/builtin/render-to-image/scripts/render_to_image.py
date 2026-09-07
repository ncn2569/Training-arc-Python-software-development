from __future__ import annotations

import argparse
import base64
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import quote

import httpx

BROWSERLESS_URL_ENV = "BROWSERLESS_URL"
MERMAID_INK_URL_ENV = "MERMAID_INK_URL"
BROWSERLESS_URL_DEFAULT = "http://localhost:3000"
MERMAID_INK_URL_DEFAULT = "http://localhost:3001"
RENDER_TIMEOUT_SECONDS = 300


def render_html(source: str, service_url: str, client: httpx.Client) -> bytes:
    response = client.post(
        f"{service_url.rstrip('/')}/screenshot",
        json={
            "html": source,
            "scrollPage": True,
            "options": {
                "fullPage": True,
                "type": "png",
            },
        },
    )
    response.raise_for_status()
    return response.content


def render_mermaid(source: str, service_url: str, client: httpx.Client) -> bytes:
    encoded = quote(
        base64.b64encode(source.strip().encode("utf-8")).decode("ascii"),
        safe="",
    )
    try:
        response = client.get(
            f"{service_url.rstrip('/')}/img/{encoded}",
            params={"type": "png", "bgColor": "!white"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        response_body = exc.response.text.strip()[:500]
        raise ValueError(
            f"Mermaid Ink returned HTTP {exc.response.status_code}: "
            f"{response_body or '<empty response>'}"
        ) from exc
    return response.content

def render_file(
    input_path: Path,
    output_path: Path,
    client: httpx.Client,
    environment: Mapping[str, str],
) -> None:
    if output_path.suffix.lower() != ".png":
        raise ValueError(f"Output path must have a .png suffix: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    source = input_path.read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError(f"Input file is empty: {input_path}")

    match input_path.suffix.lower():
        case ".html" | ".htm":
            service_url = environment.get(
                BROWSERLESS_URL_ENV, BROWSERLESS_URL_DEFAULT
            ).strip()
            if not service_url:
                raise ValueError(f"{BROWSERLESS_URL_ENV} is not configured")
            image = render_html(source, service_url, client)
        case ".mmd":
            service_url = environment.get(
                MERMAID_INK_URL_ENV, MERMAID_INK_URL_DEFAULT
            ).strip()
            if not service_url:
                raise ValueError(f"{MERMAID_INK_URL_ENV} is not configured")
            image = render_mermaid(source, service_url, client)
        case suffix:
            raise ValueError(
                f"Unsupported input suffix '{suffix}' for {input_path}; "
                "supported suffixes: .html, .htm, .mmd"
            )

    if not image.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Render service returned non-PNG content")

    output_path.write_bytes(image)

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render standalone HTML or Mermaid source to a PNG image.",
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    try:
        with httpx.Client(timeout=RENDER_TIMEOUT_SECONDS) as client:
            render_file(args.input, args.output, client, os.environ)
    except (
        UnicodeError,
        OSError,
        ValueError,
        httpx.TimeoutException,
        httpx.HTTPStatusError,
        httpx.RequestError,
    ) as exc:
        print(f"render-to-image failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
