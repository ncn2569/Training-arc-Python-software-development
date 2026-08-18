import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from io import BytesIO

from PIL import Image

from context.memory import count_tokens_by_string
from tools.path import resolve_path
from tools.render import render_file

MAX_TOKEN_PER_READ_LIMIT = 25000

IMAGE_SUFFIX = {".jpg", ".png", ".jpeg", ".gif", ".webp"}

RENDER_SUFFIX = {".html", ".mmd"}

MIME_TYPE = {
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

PILLOW_TYPE = {
    ".jpg": "JPEG",
    ".png": "PNG",
    ".jpeg": "JPEG",
    ".gif": "GIF",
    ".webp": "WEBP",
}

IMAGE_MAX_WIDTH = 2000

IMAGE_MAX_HEIGHT = 2000

IMAGE_SIZE_LIMIT = 500 * 1024


def _read_image(file_path: Path) -> dict:
    """
    Đọc ảnh trả về image_url: data:mime_type;base64,image_string
    """
    tail = file_path.suffix.lower()

    compressed_flag = False
    try:
        raw_bytes = file_path.read_bytes()

        processed_bytes, tail = _process_image(raw_bytes, tail)

        mime_type = MIME_TYPE.get(tail)

        if processed_bytes is None:
            return {
                "success": False,
                "path": str(file_path),
                "error": "Ảnh quá lớn",
                "hint": "Hãy crop ảnh ra và chọn phần ảnh cần thiết để đọc thôi, không cần đọc hết.",
            }

        # print(f"DEBUGGING {len(processed_bytes)}  {len(raw_bytes)}")

        if len(processed_bytes) != len(raw_bytes):
            compressed_flag = True

        image_string = base64.b64encode(processed_bytes).decode("utf-8")
        return {
            "success": True,
            "path": str(file_path),
            "type": "image",
            "mime_type": mime_type,
            "size_bytes": len(processed_bytes),
            "is_compressed": compressed_flag,
            "data_url": f"data:{mime_type};base64,{image_string}",
        }
    except Exception as e:
        return {"success": False, "path": str(file_path), "error": str(e)}


def _process_image(raw_bytes: bytes, tail: str) -> tuple[bytes, str]:
    """
    Hàm xử lý ảnh, resize về 1 nửa size, nếu vẫn vượt hơn size thì trả về None, tail.
    """
    img = Image.open(BytesIO(raw_bytes))

    original_width, original_height = img.size
    width, height = original_width, original_height

    if width > IMAGE_MAX_WIDTH:
        height = round((height * IMAGE_MAX_WIDTH) / width)
        width = IMAGE_MAX_WIDTH

    if height > IMAGE_MAX_HEIGHT:
        width = round((width * IMAGE_MAX_HEIGHT) / height)
        height = IMAGE_MAX_HEIGHT

    if width != original_width or height != original_height:
        img = img.resize((width, height), Image.Resampling.LANCZOS)

    buffer = BytesIO()

    pillow_type = PILLOW_TYPE.get(tail)

    if pillow_type in {"JPEG", "PNG"}:
        img.save(buffer, format=pillow_type, quality=85)
    else:
        img.save(buffer, format=pillow_type)

    if len(buffer.getvalue()) > IMAGE_SIZE_LIMIT:
        buffer.truncate(0)
        buffer.seek(0)
        pillow_type = "JPEG"
        tail = ".jpg"
        img = img.convert("RGB")
        img.save(buffer, format=pillow_type, quality=50)
        if len(buffer.getvalue()) > IMAGE_SIZE_LIMIT:
            return None, tail

    return buffer.getvalue(), tail


def _format_line_number(content: str, start_line: int = 1) -> str:
    """
    Trả về định dạng số dòng tương ứng. (ví dụ: 1: import os)
    """
    list_content = content.splitlines()
    numbered_lines = [
        f"{idx}: {line}" for idx, line in enumerate(list_content, start=start_line)
    ]
    return "\n".join(numbered_lines)


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

        if file_path.suffix.lower() in IMAGE_SUFFIX:
            return _read_image(file_path)


        if file_path.suffix.lower() in RENDER_SUFFIX and range is None:
            return render_file(file_path)


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

    path = resolve_path("super_heavy_picture.jpg")
    print(_read_image(path))
