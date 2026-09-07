---
name: focus-image-region
description: Crop a pixel-coordinate region from a workspace PNG, JPG/JPEG, or WebP image into a PNG for focused inspection. Use when a specific image area needs additional focus.
---

# Focus on an image region

Crop a rectangular region from an existing static image into a new PNG. Use
this instead of writing an ad-hoc Pillow or OpenCV script.

## Supported formats

| Direction | Supported formats |
| --- | --- |
| Input | Static PNG, JPG/JPEG, and WebP |
| Output | PNG only |

GIF, SVG, BMP, TIFF, animated WebP, APNG, and other animated images are not
supported. File suffix matching is case-insensitive.

## Coordinate contract

- `(0, 0)` is the top-left corner.
- `x` increases to the right and `y` increases downward.
- The rectangle is `[x1, x2) × [y1, y2)`.
- `x1` and `y1` are included; `x2` and `y2` are excluded.
- The rectangle must be fully inside the image; coordinates are not clamped.
- The crop size is `x2 - x1` by `y2 - y1`.
- JPEG EXIF orientation is applied before dimensions and coordinates are
  evaluated.

## Usage

When the region is not already known, consider using `read_file` to inspect the
current image before choosing coordinates.

Run the script with absolute paths inside this project's `workspace/` and named flags:

```bash
python scripts/crop_image.py \
  --input /absolute/path/to/source.png \
  --x1 100 \
  --y1 200 \
  --x2 900 \
  --y2 700 \
  --output /absolute/path/to/source-focus.png
```

A successful command prints one compact JSON object containing `output_path`,
`source_size`, `crop_box`, and `crop_size`. It never prints image data or
base64.

After cropping, consider using `read_file` with `output_path` when inspecting
the focused visual content would help the current task. This is optional; the
reported metadata may already be sufficient.

For a deeper focus, the output can be used as the next input. Coordinates then
refer to that cropped image and begin again at `(0, 0)`. Prefer a new output
path when earlier crop levels should be retained.
