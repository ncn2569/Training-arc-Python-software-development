---
name: render-to-image
description: Render local HTML, HTM, or Mermaid (`.mmd`) files to full-page PNG images through Browserless, then split unusually tall results into vertical tiles. Use when an agent needs a visual preview, a render check, or image output for these local file types. Do not use for PDFs, SVG conversion, or screenshots of remote website URLs.
---

# Render local markup to PNG

Use the scripts in this skill instead of assembling Browserless requests by hand. The scripts keep validation, render readiness, and output naming consistent while ensuring binary image data never enters the model context.

## Workflow

Run these steps in order. Each step prevents a later, more expensive failure and produces a short text summary suitable for tool output.

1. **Prove Browserless can actually render.** Run `check_browserless.py` before inspecting or changing the input. A TCP-only health check can pass while Chromium or `/screenshot` is broken, so this command renders a minimal page through the same endpoint used later.
2. **Validate the source.** Run `validate_input.py` before calling Browserless. This catches unsupported, empty, non-UTF-8, fenced Mermaid, and structurally invalid inputs without spending a browser session.
3. **Render one full-page PNG.** Run `render.py`. HTML/HTM is sent as authored. Mermaid is placed in the fixed template and Browserless waits for Mermaid's ready flag, because taking the screenshot at page load can capture a blank or half-rendered diagram.
4. **Normalize the final image set.** Run `tile_image.py` on the full-page PNG. Very tall images are awkward for viewers and can exceed downstream image limits, so this step emits bounded-height vertical tiles while preserving every pixel.

```bash
python scripts/check_browserless.py --timeout 10
python scripts/validate_input.py --input /absolute/path/to/source.mmd
python scripts/render.py --input /absolute/path/to/source.mmd --output /absolute/path/to/scratch/source.full.png
python scripts/tile_image.py --input /absolute/path/to/scratch/source.full.png --output-dir /absolute/path/to/output --output-stem source
```

Use absolute paths so the produced files are unambiguous across agent and session workspaces. `--browserless-url` overrides `BROWSERLESS_URL`; otherwise the scripts use `http://localhost:3001`.

## Stop and retry rules

- If the connection check fails, stop. Report the actionable error and do not retry render calls against the same unavailable endpoint.
- If validation fails, fix the source once and validate again. Do not render an input that still fails validation.
- If Browserless reports a Mermaid/runtime error, fix the diagram rather than accepting a blank image. Do not silently fall back to raw text.
- Do not print, base64-encode, or `read_file` a PNG. Return its path and use an image-capable viewer when visual inspection is needed.

## References

- Read [references/browserless.md](references/browserless.md) when configuring the endpoint or diagnosing connection, timeout, readiness, HTTP, or response-format failures.
- Read [references/output-contract.md](references/output-contract.md) when choosing render options, integrating the scripts, or consuming tiled output.

## Scripts

All options are documented by `--help`. Always pass named flags.

- `scripts/check_browserless.py` — verify `/screenshot` end to end.
- `scripts/validate_input.py` — validate `.html`, `.htm`, or `.mmd` source.
- `scripts/render.py` — create one full-page PNG through Browserless.
- `scripts/tile_image.py` — copy a normal-height PNG or split a tall PNG into numbered vertical tiles.
