# Browserless rendering contract

Read this reference when configuring Browserless or diagnosing a failed connection/render.

## Endpoint resolution

All Browserless-aware scripts resolve the base URL in this order:

1. `--browserless-url`
2. `BROWSERLESS_URL`
3. `http://localhost:3001`

The default matches the repository's Docker Compose host mapping. A process running inside another container should normally set `BROWSERLESS_URL=http://browserless:3000`.

## Why the connection check renders a page

`check_browserless.py` posts minimal HTML to `<base-url>/screenshot` and verifies a PNG response. This detects a reachable HTTP port whose Chromium worker, screenshot route, or response encoding is broken. Run it once per workflow; repeated failures against unchanged configuration do not add information.

The render request uses Browserless's raw `html` input and Puppeteer screenshot options:

```json
{
  "html": "<!doctype html>...",
  "options": { "fullPage": true, "type": "png" },
  "viewport": {
    "width": 1440,
    "height": 900,
    "deviceScaleFactor": 1
  }
}
```

Mermaid requests also include:

```json
{
  "waitForFunction": {
    "fn": "() => window.__RENDER_READY__ === true",
    "timeout": 30000
  }
}
```

This predicate prevents Browserless from racing the asynchronous CDN import and Mermaid layout.

## Failure interpretation

- **Could not reach Browserless** — confirm the process context, URL/port, and container status before retrying.
- **HTTP 4xx/5xx** — read the returned detail. For Mermaid, parse/runtime failures commonly surface as a readiness timeout.
- **Unexpected content type or PNG signature** — the configured endpoint is not returning the screenshot API's binary PNG response.
- **Readiness timeout** — confirm CDN access and fix invalid Mermaid. Do not accept a blank screenshot.

The scripts intentionally fail without writing the requested render output when the response is invalid.
