import base64
import os
import subprocess
import tempfile
from base64 import b64encode
from pathlib import Path

import requests
import yaml


def send_to_browserless(html_content, output_path, wait_ms=2000):
    """
    html_content: chuỗi HTML hoàn chỉnh
    output_path:  đường dẫn file ảnh output (vd: "output/display.png")
    wait_ms:      thời gian chờ JS render (Mermaid cần thời gian để vẽ)
    """
    url = "http://localhost:3000/screenshot"  # api screenshot của browserless

    payload = {
        "html": html_content,
        "options": {
            "fullPage": True,
        },
        "gotoOptions": {"waitUntil": "networkidle0", "timeout": 30000},
        "addScriptTag": [],
    }
    resp = requests.post(url, json=payload, timeout=60)

    resp.raise_for_status()

    ### resp.content == raw_bytes ảnh -> 

    # mime_type = resp.headers.get("Content-Type") # -> mime_type
    # print(mime_type)

    with open(output_path, "wb") as f:
        f.write(resp.content)

    url_string = base64.b64encode(resp.content).decode("utf-8")


def render_display(yaml_data, output_dir="output"):
    html = yaml_data.get("display", "")
    send_to_browserless(html, f"{output_dir}/html_render.png")


def render_mermaid_cli(mermaid_code, output_path):
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".mmd", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(mermaid_code)
        tmp_path = tmp.name
    try:
        subprocess.run(
            [
                "mmdc",
                "-i",
                tmp_path,
                "-o",
                output_path,
                "-w",
                "1920",
                "-H",
                "1080",
                "--backgroundColor",
                "white",
            ],
            check=True,
            shell=True,
        )

    finally:
        os.unlink(tmp_path)


def render_all_mermaid(yaml_data, output_dir="output"):
    diagrams = yaml_data.get("diagrams", {})
    os.makedirs(output_dir, exist_ok=True)

    for name, data in diagrams.items():
        code = data.get("code", "")
        safe_name = name.replace(" ", "_").lower()
        output_path = f"{output_dir}/{safe_name}.png"

        render_mermaid_cli(code, output_path)


def main():
    with open("project.yaml","r",encoding="utf-8") as f:
        data=yaml.safe_load(f)

    render_display(data)

    render_all_mermaid(data)



if __name__=="__main__":
    main()