import base64
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

sys.path.insert(0, str(Path(__file__).parent.parent))

from context.memory import count_tokens_by_string
from tools.path import resolve_path

MAX_TOKEN_PER_READ_LIMIT = 25000

IMAGE_SUFFIX = {".jpg", ".png", ".jpeg", ".gif", ".webp"}
MIME_TYPE = {".jpg": "image/jpeg", ".png": "image/png", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
PILLOW_TYPE = {".jpg": "JPEG", ".png": "PNG", ".jpeg": "JPEG", ".gif": "GIF", ".webp": "WEBP"}

# Ảnh giờ thuộc về tool `read_image` (tools/image.py) — đọc ảnh + crop vùng.


def _format_line_number(content: str, start_line: int = 1) -> str:
    """
    Trả về định dạng số dòng tương ứng. (ví dụ: 1: import os)
    """
    list_content = content.splitlines()
    numbered_lines = [
        f"{idx}: {line}" for idx, line in enumerate(list_content, start=start_line)
    ]
    return "\n".join(numbered_lines)


def _read_image(file_path: Path, requested_path: str) -> dict:
    """Return complete image content for the unified read_file tool."""
    try:
        suffix = file_path.suffix.lower()
        with Image.open(file_path) as opened:
            image = ImageOps.exif_transpose(opened) or opened
            width, height = image.size
            if PILLOW_TYPE[suffix] == "JPEG" and image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            buffer = BytesIO()
            image.save(buffer, format=PILLOW_TYPE[suffix])

        return {
            "success": True,
            "type": "image",
            "path": requested_path,
            "mime_type": MIME_TYPE[suffix],
            "image_width": width,
            "image_height": height,
            "size_bytes": file_path.stat().st_size,
            "data_url": f"data:{MIME_TYPE[suffix]};base64,{base64.b64encode(buffer.getvalue()).decode('ascii')}",
        }
    except UnidentifiedImageError:
        return {"success": False, "path": requested_path, "error": "INVALID IMAGE"}


def read_file(
    path: str, range: tuple[int, int] | None = None, limit: int | None = None
) -> dict:
    """
    Tool đọc file, có hỗ trợ đọc theo dòng và có limit về số dòng trả về.
    """
    try:
        file_path = resolve_path(path)
        if not file_path.exists():
            return {"success": False, "path": path, "error": "FILE NOT FOUND"}

        # Unified reader: image suffixes are delegated internally, not exposed as tools.
        if file_path.suffix.lower() in IMAGE_SUFFIX:
            return _read_image(file_path, path)

        # Legacy direct-tool redirect kept disabled while testing unified read_file.
        if False and file_path.suffix.lower() in IMAGE_SUFFIX:
            # Ảnh đã tách sang tool `read_image` — chuyển hướng để agent dùng đúng tool.
            return {
                "success": False,
                "path": path,
                "error": "Đây là file ảnh. Hãy dùng tool `read_image(file_path)` để đọc ảnh (hỗ trợ crop vùng bằng x1, y1, x2, y2).",
            }


        # if file_path.suffix.lower() in RENDER_SUFFIX and range is None:
        #     return render_file(file_path)


        file_content = file_path.read_text(encoding="utf-8")
        all_lines = file_content.splitlines()
        selected_lines = all_lines
        start_line = 1
        total_lines = len(all_lines)

        if total_lines == 0:
            return {
                "success": True,
                "path": path,
                "notice": "File exists but is empty.",
                "total_lines": 0,
                "content": "",
            }

        if range is not None:
            start_line, end_line = range
            if start_line > total_lines:
                return {
                    "success": False,
                    "path": path,
                    "error": f"Offset {start_line} exceeds total lines ({total_lines}).",
                    "total_lines": total_lines,
                }
            selected_lines = all_lines[start_line - 1 : end_line]

        if limit is not None and limit > 0:
            selected_lines = selected_lines[:limit]

        result_content = ""
        truncated = False
        lines_included = 0
        for i, line in enumerate(selected_lines):
            if count_tokens_by_string(line) > MAX_TOKEN_PER_READ_LIMIT:
                curr_line_idx = start_line + i
                return {
                    "success": False,
                    "path": path,
                    "line_number": curr_line_idx,
                    "error": (
                        f"Line {curr_line_idx} alone exceeds token limit "
                        f"({count_tokens_by_string(line)} > {MAX_TOKEN_PER_READ_LIMIT}). "
                        f"Use grep_search to find specific content instead."
                    ),
                    "total_lines": total_lines,
                }

            accumulate_content = (
                result_content + ("\n" if result_content else "") + line
            )

            if count_tokens_by_string(accumulate_content) > MAX_TOKEN_PER_READ_LIMIT:
                truncated = True
                break

            result_content = accumulate_content
            lines_included += 1

        # xử lý 3 case: không truncated -> trả về như bình thường,
        # truncated với range + limit -> hướng dẫn thu hẹp range hoặc dùng cách khác
        # đọc file thuần không range hay limit -> partial view + hướng dẫn cách đọc
        range_limit_intent = range is not None or limit is not None

        if range_limit_intent and truncated:
            return {
                "success": False,
                "path": path,
                "error": (
                    f"Read range [{start_line}:{start_line + lines_included - 1}] "
                    f"exceeds token limit ({count_tokens_by_string(result_content)} > {MAX_TOKEN_PER_READ_LIMIT}). "
                    f"Use a smaller range or limit."
                ),
                "total_lines": total_lines,
                "lines_returned": lines_included,
                "hint": "Use a smaller range (e.g. range=[start, start+100]) or grep_search to target specific content.",
            }
        elif truncated:
            return {
                "success": True,
                "path": path,
                "total_lines": total_lines,
                "lines_returned": lines_included,
                "truncated": True,
                "token_count": count_tokens_by_string(result_content),
                "notice": (
                    f"PARTIAL VIEW: Showing first {lines_included} of {total_lines} lines. "
                    f"Use range=[{lines_included + 1}, N] or limit=N to read more."
                ),
                "content": _format_line_number(result_content, start_line),
            }
        else:
            return {
                "success": True,
                "path": path,
                "total_lines": total_lines,
                "lines_returned": lines_included,
                "truncated": False,
                "token_count": count_tokens_by_string(result_content),
                "content": _format_line_number(result_content, start_line),
            }
    except Exception as e:
        return {"success": False, "path": path, "error": str(e)}


if __name__ == "__main__":
    # # print(read_file("sqlite3.c"))
    # [TẮT] đọc ảnh của read_file
    # path = resolve_path("super_heavy_picture.jpg")
    # print(_read_image(path))
    pass
