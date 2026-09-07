import base64
import httpx
from pathlib import Path
from textwrap import dedent
from urllib.parse import quote

BROWSERLESS_URL = "http://localhost:3000"
MERMAID_INK_URL = "http://localhost:3001"

def render_html(
    source: str,
    service_url: str,
    client: httpx.Client,
) -> bytes:
    payload: dict[str, object] = {
        "html": source,
        "scrollPage": True,
        "options": {
            "fullPage": True,
            "type": "png",
        },
    }
    response = client.post(
        f"{service_url.rstrip('/')}/screenshot",
        json=payload,
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
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        response_body = exc.response.text.strip()[:500]
        raise ValueError(
            f"Mermaid Ink returned HTTP {exc.response.status_code}: "
            f"{response_body}"
        ) from exc
    return response.content


if __name__ == "__main__":
    html = """
    <!doctype html>
    <html><body><h1>Browserless OK</h1><p>Ảnh này được render từ HTML.</p></body></html>
    """
    # This HTML is NOT self-contained: its stylesheet and image are on the Internet.
    html_external_assets = """
    <!doctype html>
    <html>
      <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
      </head>
      <body>
        <main class="container">
          <h1>External assets</h1>
          <p>CSS and this image are downloaded by Browserless.</p>
          <img src="https://picsum.photos/720/240" alt="A random remote image">
        </main>
      </body>
    </html>
    """
    # This image exists next to temp2.py on Windows, but not inside Browserless.
    html_local_image_not_embedded = """
    <!doctype html>
    <html>
      <body>
        <h1>Local image, not embedded</h1>
        <p>Browserless cannot resolve this relative path:</p>
        <img src="./architecture_overview.png" alt="Local image did not load">
      </body>
    </html>
    """
    # A long page: fullPage=True will produce one tall PNG instead of a viewport PNG.
    html_large = """
    <!doctype html>
    <html>
      <head>
        <style>
          body { margin: 0; font: 24px Arial, sans-serif; }
          section { height: 500px; box-sizing: border-box; padding: 48px; color: white; }
          section:nth-child(odd) { background: #2563eb; }
          section:nth-child(even) { background: #7c3aed; }
        </style>
      </head>
      <body>
        <section><h1>Large HTML test</h1><p>Each section is 500 px tall.</p></section>
        %s
      </body>
    </html>
    """ % "".join(
        f"<section><h2>Section {number}</h2><p>Browserless renders this into one long PNG.</p></section>"
        for number in range(1, 17)
    )
    # The content changes only after JavaScript finishes its delayed "fetch".
    html_dynamic = """
    <!doctype html>
    <html>
      <body>
        <h1>Dynamic HTML test</h1>
        <p id="status">Loading data...</p>
        <script>
          setTimeout(() => {
            document.querySelector("#status").textContent = "Data loaded: 42 orders";
          }, 1500);
        </script>
      </body>
    </html>
    """
    mermaid = """
---
config:
    theme: neutral
    flowchart:
        curve: basis
---
flowchart LR
    A[Python] --> B[Mermaid Ink]
    B --> C[PNG]
"""
    mermaid = """
---
config:
    theme: neutral
    flowchart:
        curve: basis
---
flowchart LR
    A[Python] --> B[Mermaid Ink]
    B --> C[PNG]
"""

    mermaid_error = """
---
config:
    theme: neutral
    flowchart:
        curve: basis
---
flowchart LR
    A[Python] --> B[Mermaid Ink]
    B --> C[PNG]
"""
    with httpx.Client(timeout=60) as client:
        try:
            Path("browserless-test.png").write_bytes(
                render_html(html, BROWSERLESS_URL, client)
            )
            Path("browserless-external-assets-test.png").write_bytes(
                render_html(html_external_assets, BROWSERLESS_URL, client)
            )
            Path("browserless-local-image-not-embedded-test.png").write_bytes(
                render_html(html_local_image_not_embedded, BROWSERLESS_URL, client)
            )
            Path("browserless-large-test.png").write_bytes(
                render_html(html_large, BROWSERLESS_URL, client)
            )
            Path("mermaid-test.png").write_bytes(
                render_mermaid(mermaid, MERMAID_INK_URL, client)
            )
            Path("mermaid-test_error.png").write_bytes(
                render_mermaid(mermaid_error, MERMAID_INK_URL, client)
            )
        except Exception as e:
            print(str(e))
        else:
            print("Xong")