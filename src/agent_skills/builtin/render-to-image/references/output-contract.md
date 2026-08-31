# Input and output contract

Read this reference when selecting CLI options, invoking the full workflow, or consuming tiled output.

## Inputs

- Accepted extensions: `.html`, `.htm`, `.mmd` (case-insensitive).
- Source encoding: UTF-8 and non-empty.
- HTML/HTM must contain markup rather than plain text.
- Mermaid files contain only the diagram body, beginning with a supported diagram declaration. Markdown fences are invalid because the fixed HTML template supplies the document wrapper.

The renderer accepts local files only. It does not navigate to remote URLs, convert PDF/SVG files, compile local HTML assets, or rewrite the source.

## Render defaults

| Option | Default | Reason |
| --- | ---: | --- |
| `--viewport-width` | 1440 | Stable desktop layout |
| `--viewport-height` | 900 | Stable initial layout; output remains full-page |
| `--device-scale-factor` | 1 | Predictable pixel dimensions and memory use |
| `--timeout` | 30 seconds | Bounds Browserless and Mermaid readiness waits |
| Screenshot type | PNG | Lossless text and diagram edges |
| Background | White | Deterministic output for HTML and Mermaid |

The Mermaid template is fixed at `scripts/templates/mermaid.html`. It pins Mermaid, JSON-escapes the source before insertion, renders into `#diagram`, and sets `window.__RENDER_READY__` only after SVG creation succeeds.

## Final image naming

Run render into scratch, then run tiling into the destination directory:

```bash
python scripts/render.py \
  --input /workspace/chart.mmd \
  --output /workspace/scratch/chart.full.png

python scripts/tile_image.py \
  --input /workspace/scratch/chart.full.png \
  --output-dir /workspace/output \
  --output-stem chart \
  --max-tile-height 8000
```

- Height `<= --max-tile-height`: `/workspace/output/chart.png`
- Height `> --max-tile-height`: `/workspace/output/chart.tile-001.png`, `chart.tile-002.png`, ...

Tiles preserve the original width, cover the image from top to bottom without overlap or gaps, and allow only the last tile to be shorter than the threshold. The full-page scratch image is not deleted; the caller controls scratch cleanup.
