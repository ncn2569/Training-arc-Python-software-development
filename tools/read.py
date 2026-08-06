from tools.path import resolve_path


def _format_line_number(content: str) -> str:
    """
    Trả về định dạng số dòng tương ứng. (ví dụ: 1: import os)
    """
    list_content = content.splitlines()
    for idx, line in enumerate(list_content, start=1):
        numbered_lines = f"{idx}: {line}"
    return "\n".join(numbered_lines)


def read_file(path: str, range: tuple[int, int] | None = None) -> dict:
    """
    Tool đọc file, có hỗ trợ đọc theo dòng và có limit về số dòng trả về.
    """
    try:
        file_path = resolve_path(path)
        if not file_path.exists():
            return {"success": False, "path": path, "error": "FILE NOT FOUND"}
            
        file_content = file_path.read_text(encoding="utf-8") #####

        all_lines = file_content.splitlines()

        total_lines = len(all_lines)

        if range is not None:
            start_line, end_line = range

            all_lines = all_lines[start_line - 1 : end_line]

        result_content = "\n".join(all_lines)

        return {
            "success": True,
            "content": _format_line_number(result_content),
            "total_lines": total_lines,
            "lines_returned": len(all_lines)
        }
    except Exception as e:
        return {"success": False, "path": path, "error": str(e)}
