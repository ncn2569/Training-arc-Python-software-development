import base64
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.path import resolve_path

BROWSERLESS_URL = "http://localhost:3000/screenshot"

# nghĩ
MERMAID_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'default' });
    </script>
    <style>
        body {
                {
                margin: 0;
                background: white;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                font-family: sans-serif;
            }
        }

        .mermaid {
                {
                display: block;
            }
        }
    </style>
</head>

<body>
    <div class="mermaid">
        __MERMAID_CODE__
    </div>
</body>

</html>
"""


# nghĩ về timimng của mmd
def _send_to_browserless(html_content: str) -> tuple[str, str]:  # nghĩ
    """
    Gửi HTML tới browserless để render. Trả về bytes ảnh PNG.
    """
    payload = {
        "html": html_content,
        "options": {
            "type": "png",  # nghĩ
            "fullPage": True,
        },
        "gotoOptions": {
            "waitUntil": "networkidle0",
            "timeout": 300000,
        },
    }
    resp = requests.post(BROWSERLESS_URL, json=payload, timeout=60)
    resp.raise_for_status()

    # test_path = Path("test.png")
    # test_path = resolve_path(str(test_path))
    # with open(test_path, "wb") as f:
    #     f.write(resp.content)

    return resp.content, resp.headers.get("Content-Type")


def render_file(path: Path) -> dict:
    """
    Render file .html hoặc .mmd thành ảnh PNG rồi trả về data_url
    """
    try:

        suffix = path.suffix.lower()
        content = path.read_text(encoding="utf-8")

        if suffix == ".html":
            html_content = content

        elif suffix == ".mmd": 
            html_content = MERMAID_HTML_TEMPLATE.replace("__MERMAID_CODE__", content)

        else:
            return {
                "success": False,
                "error": f"Định dạng không hỗ trợ: {suffix}. Chỉ hỗ trợ .html, .mmd",
            }

        image_bytes, mime_type = _send_to_browserless(html_content)

        image_string = base64.b64encode(image_bytes).decode(encoding="utf-8")

        return {
            "success": True,
            "path": str(path),
            "type": "image",
            "mime_type": "image/png",
            "size_bytes": len(image_bytes),
            "data_url": f"data:{mime_type};base64,{image_string}",
        }
    except Exception as e:
        return {"success": False, "error": str(e), "path": str(path)}


if __name__ == "__main__":
    path = Path("project_visualization.html")
    path=resolve_path(path)
    render_file(path)
