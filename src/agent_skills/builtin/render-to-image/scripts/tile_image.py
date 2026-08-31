#!/usr/bin/env python3
"""Normalize a rendered PNG into one image or bounded-height vertical tiles."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError


def tile_image(
    input_path: Path,
    output_dir: Path,
    output_stem: str,
    max_tile_height: int,
) -> tuple[tuple[int, int], list[Path]]:
    if not input_path.is_file():
        raise ValueError(f"input image not found: {input_path}")
    if input_path.suffix.lower() != ".png":
        raise ValueError(f"--input must be a PNG file: {input_path}")
    if not output_stem or Path(output_stem).name != output_stem:
        raise ValueError("--output-stem must be a non-empty filename stem, not a path")

    try:
        with Image.open(input_path) as opened:
            opened.verify()
        with Image.open(input_path) as opened:
            image = opened.copy()
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"input is not a valid PNG image: {input_path}") from exc

    width, height = image.size
    if width <= 0 or height <= 0:
        raise ValueError("input image has invalid dimensions")
    output_dir.mkdir(parents=True, exist_ok=True)

    if height <= max_tile_height:
        output_path = output_dir / f"{output_stem}.png"
        shutil.copyfile(input_path, output_path)
        return (width, height), [output_path]

    outputs: list[Path] = []
    for index, top in enumerate(range(0, height, max_tile_height), start=1):
        bottom = min(top + max_tile_height, height)
        tile = image.crop((0, top, width, bottom))
        output_path = output_dir / f"{output_stem}.tile-{index:03d}.png"
        tile.save(output_path, format="PNG")
        outputs.append(output_path)
    return (width, height), outputs


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy a normal-height PNG or split a tall PNG into vertical tiles."
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Full-page PNG to inspect"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for normalized output images",
    )
    parser.add_argument(
        "--output-stem", required=True, help="Filename stem for output images"
    )
    parser.add_argument(
        "--max-tile-height",
        type=positive_int,
        default=8000,
        help="Maximum output tile height in pixels (default: 8000)",
    )
    args = parser.parse_args()

    try:
        dimensions, outputs = tile_image(
            args.input,
            args.output_dir,
            args.output_stem,
            args.max_tile_height,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    output_list = ",".join(str(path) for path in outputs)
    print(
        f"tiled width={dimensions[0]} height={dimensions[1]} count={len(outputs)} outputs={output_list}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
