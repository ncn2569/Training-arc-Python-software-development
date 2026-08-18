from tools.path import resolve_path


def write_file(path: str, content: str) -> dict:
    """
    Có thể create file mới với nội dung nếu file chưa tồn tại hoặc là overwrite toàn bộ file đã tồn tại. 
    """
    try:
        target_path = resolve_path(path)

        existed = target_path.exists()

        action = "OVERWRITE" if existed else "CREATE"

        target_path.parent.mkdir(parents=True, exist_ok=True)

        target_path.write_text(content, encoding="utf-8")

        bytes_written = len(content.encode("utf-8"))

        return {
            "success": True,
            "path": path,
            "bytes_written": bytes_written,
            "action": action
        }
    except Exception as e:
        return {"success": False, "path": path, "error": str(e)}
