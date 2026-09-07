---
name: render-to-image
description: Render HTML (.html/.htm) and Mermaid (.mmd) source files into PNG images. Use when an existing source file needs to be visualized or inspected as an image.
---

# Render HTML or Mermaid source to PNG

Render one supported source file into one PNG. The source may come from any
workflow; only the input contract below matters. The script uses Browserless
for HTML and Mermaid Ink for Mermaid.

## Source Preparation

| Input | Before rendering |
| --- | --- |
| HTML with local images, fonts, or CSS | Make those assets reachable to Browserless before rendering, preferably by producing self-contained HTML. |
| Mermaid that needs authoring or repair | Author or repair the Mermaid source before rendering. |

Prepare source directly when practical. If available, `html-yaml-embed` can
optionally compile HTML into a self-contained document, and `mermaid-diagrams`
can optionally help author or repair raw Mermaid. Neither skill is a dependency,
and the source does not need to originate from an artifact workflow.

## Input contract

The input must:

- be a non-empty UTF-8 text file;
- use `.html`, `.htm`, or `.mmd` as its suffix;
- contain only valid source for its format. Extract embedded source before
  invoking the renderer.

The output path must end in `.png`. The input and output may live anywhere the
sandbox can access.

## Result and failure behavior

- Exit 0 means the render request succeeded and the output file was written.
- Before writing the output, the script verifies that the service response has
  a PNG signature. A successful HTTP response containing HTML, JSON, or another
  non-PNG payload is treated as a failure.
- The script does not modify the input or resize the returned image.
- For invalid source, repair or prepare the source before retrying.
- For service/network failures, do not repeat an identical request without reason.

## Reference files

Read only the reference matching the input suffix before preparing or repairing
source:

- For `.html` or `.htm`, read [HTML input](references/html-input.md) for
  document shape, assets, JavaScript, and Browserless behavior.
- For `.mmd`, read [Mermaid input](references/mermaid-input.md) for raw
  source boundaries, examples, frontmatter, and Mermaid Ink behavior.
- `scripts/render_to_image.py` — the single HTML/Mermaid render command.

## Scripts

Run these from this skill directory. Always pass named flags; do not use positional arguments.

```bash
python D:\Inter-K\src\agent_skills\builtin\render-to-image\scripts\render_to_image.py \
  --input /absolute/path/to/source.html \
  --output /absolute/path/to/source.png
```

Use the same command for `.mmd`; the suffix performs dispatch. Wait for exit 0
before using the output.
