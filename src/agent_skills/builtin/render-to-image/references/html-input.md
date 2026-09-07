# HTML input for Browserless

Prefer a standalone UTF-8 `.html` or `.htm` file. Browserless receives the file
contents as an HTML string; it does not open the source file and has no base URL
pointing to the source directory. The file may come from any workflow; it does
not need to originate from an artifact or another skill.

## Preferred input

For the most reliable render, prefer HTML that:

- contains the complete visual state in one document;
- embeds local images, fonts, and CSS;
- does not require user interaction;
- does not depend on authenticated or private resources;
- reaches its intended visual state immediately after load.

## Document shape

A fragment such as `<section>...</section>` can render, but prefer a complete
document when authoring new input. A document makes encoding, default styles,
and layout intent explicit:

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Render test</title>
</head>
<body>
  <main>
    <h1>Render test</h1>
    <p>This document is ready for Browserless.</p>
  </main>
</body>
</html>
```

Save only HTML source in the file; do not include Markdown fences or explanatory text.

## Assets and URLs

Because the HTML has no filesystem base URL, choose asset forms Browserless can
actually resolve:

| Asset form | Expected behavior |
| --- | --- |
| Inline CSS and JavaScript | Reliable. |
| Inline SVG markup | Reliable and preferable to a local SVG file. |
| `data:` URI images, fonts, and stylesheets | Reliable and self-contained. |
| Public HTTPS URL | Works when Browserless can reach it and it needs no caller credentials. |
| Relative path such as `./logo.png` | Unreliable; there is no source-directory base URL. |
| `file://` or absolute sandbox path | Unreliable; Browserless runs in another service. |
| Private or authenticated resource | Do not rely on availability; access depends on the Browserless network environment and credentials. |

Prepare these assets directly when practical. If the `html-yaml-embed` skill is
available, its compile workflow is an optional way to produce self-contained
HTML; rendering does not require YAML embedding or that skill.

## JavaScript and rendering time

Browserless executes JavaScript and may load network resources, but this skill
does not configure a viewport, a custom wait condition, clicks, input, cookies,
or authentication. Keep first paint self-contained and deterministic:

- render the final state directly rather than requiring user interaction;
- avoid animations or disable them in CSS;
- do not make essential content depend on a slow asynchronous request;
- use public HTTPS dependencies only when remote access is acceptable.

The request captures a full-page PNG. Natural page length determines output
height; this skill does not crop, tile, resize, or cap dimensions.

## Diagnose incomplete renders

An HTTP-successful screenshot can still show missing fonts, broken images, or a
loading state. The skill does not inspect browser console output or scan the
rendered pixels. When the page is incomplete:

1. Replace local paths with inline content, `data:` URIs, or compiled HTML.
2. Remove authentication and caller-private-network dependencies.
3. Make the desired state available at initial render without interaction.
4. Render the corrected standalone file once more.
