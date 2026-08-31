#!/usr/bin/env python3
"""Validate source files accepted by render-to-image."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SUPPORTED_SUFFIXES = {".html", ".htm", ".mmd"}
HTML_TAG_RE = re.compile(r"<[A-Za-z][^>]*>")
MERMAID_DECLARATION_RE = re.compile(
    r"^(?:---[\s\S]*?---\s*)?(?:flowchart|graph|sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram|journey|gantt|pie|gitGraph|mindmap|timeline|quadrantChart|xychart-beta|block-beta|packet-beta|architecture-beta|C4Context|C4Container|C4Component|C4Dynamic|C4Deployment)\b",
    re.MULTILINE,
)


def validate_input(input_path: Path) -> str:
    if not input_path.is_file():
        raise ValueError(f"input file not found: {input_path}")
    suffix = input_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(
            f"unsupported input extension {suffix or '(none)'}; expected one of: {supported}"
        )
    try:
        source = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"input must be valid UTF-8: {input_path}") from exc
    if not source.strip():
        raise ValueError(f"input file is empty: {input_path}")

    if suffix in {".html", ".htm"}:
        if HTML_TAG_RE.search(source) is None:
            raise ValueError("HTML input must contain at least one markup element")
        return "html"

    if "```" in source:
        raise ValueError(
            "Mermaid input must contain only the diagram body, without Markdown fences"
        )
    if MERMAID_DECLARATION_RE.search(source.lstrip()) is None:
        raise ValueError(
            "Mermaid input must start with a supported diagram declaration"
        )
    return "mermaid"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a local HTML, HTM, or Mermaid source before rendering."
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Source .html, .htm, or .mmd file"
    )
    args = parser.parse_args()

    try:
        source_type = validate_input(args.input)
        size = args.input.stat().st_size
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"valid type={source_type} bytes={size} input={args.input}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
