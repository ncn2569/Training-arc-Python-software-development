from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "workspace" / "temp3-crop-fixture.png"
OUTPUT = ROOT / "workspace" / "crops" / "temp3-skill-crop.png"
SCRIPT = ROOT / "src" / "agent_skills" / "builtin" / "focus-image-region" / "scripts" / "crop_image.py"


def main() -> int:
    image = Image.new("RGB", (1200, 800), "#e7edff")
    draw = ImageDraw.Draw(image)
    draw.rectangle((150, 100, 1000, 650), fill="#3b2cc8")
    draw.ellipse((450, 250, 750, 550), fill="#ff287b")
    image.save(INPUT)

    command = [sys.executable, str(SCRIPT), "--input", str(INPUT), "--x1", "200", "--y1", "120", "--x2", "900", "--y2", "650", "--output", str(OUTPUT)]
    result = subprocess.run(command, text=True, capture_output=True)
    print(result.stdout or result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
