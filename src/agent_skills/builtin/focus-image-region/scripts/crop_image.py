from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

SUPPORTED_INPUT_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})
PNG_COMPATIBLE_MODES = frozenset({"1", "L", "LA", "I", "I;16", "P", "RGB", "RGBA"})
WORKSPACE = Path(__file__).resolve().parents[5] / "workspace"


def require_workspace_path(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(WORKSPACE.resolve()):
        raise ValueError(f"{label} must be inside workspace: {WORKSPACE}")
    return resolved


def crop_image(
    input_path: Path,
    output_path: Path,
    crop_box: tuple[int, int, int, int],
) -> tuple[tuple[int, int], tuple[int, int]]:
    if not input_path.is_absolute() or not output_path.is_absolute():
        raise ValueError("Input and output paths must be absolute")
    input_path = require_workspace_path(input_path, "Input path")
    output_path = require_workspace_path(output_path, "Output path")
    if input_path.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
        raise ValueError(
            f"Unsupported input format '{input_path.suffix}'; "
            "supported input formats: PNG, JPG/JPEG, WebP"
        )
    if output_path.suffix.lower() != ".png":
        raise ValueError("Output format must be PNG")
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Input and output paths must be different")
    if not input_path.is_file():
        raise ValueError(f"Input image does not exist: {input_path}")

    x1, y1, x2, y2 = crop_box

    with Image.open(input_path) as source:
        if getattr(source, "n_frames", 1) != 1:
            raise ValueError("Animated images are not supported")

        visual = ImageOps.exif_transpose(source)
        try:
            visual.load()
            source_width, source_height = visual.size

            if not (0 <= x1 < x2 <= source_width and 0 <= y1 < y2 <= source_height):
                raise ValueError(
                    "Crop box must satisfy "
                    f"0 <= x1 < x2 <= {source_width} and "
                    f"0 <= y1 < y2 <= {source_height}; "
                    f"received ({x1}, {y1}, {x2}, {y2})"
                )

            cropped = visual.crop(crop_box)
        finally:
            visual.close()

    if cropped.mode not in PNG_COMPATIBLE_MODES:
        converted = cropped.convert("RGB")
        cropped.close()
        cropped = converted

    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)

    try:
        cropped.save(temporary_path, format="PNG")
        temporary_path.replace(output_path)
    finally:
        cropped.close()
        temporary_path.unlink(missing_ok=True)

    return (
        (source_width, source_height),
        (x2 - x1, y2 - y1),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Crop a pixel-coordinate image region into a PNG.",
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--x1", required=True, type=int)
    parser.add_argument("--y1", required=True, type=int)
    parser.add_argument("--x2", required=True, type=int)
    parser.add_argument("--y2", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    crop_box = (args.x1, args.y1, args.x2, args.y2)

    try:
        source_size, crop_size = crop_image(
            args.input,
            args.output,
            crop_box,
        )
    except (Image.DecompressionBombError, OSError, ValueError) as exc:
        print(f"focus-image-region failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "output_path": str(args.output),
                "source_size": {
                    "width": source_size[0],
                    "height": source_size[1],
                },
                "crop_box": {
                    "x1": args.x1,
                    "y1": args.y1,
                    "x2": args.x2,
                    "y2": args.y2,
                },
                "crop_size": {
                    "width": crop_size[0],
                    "height": crop_size[1],
                },
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
