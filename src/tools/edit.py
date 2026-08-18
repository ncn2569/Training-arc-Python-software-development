from tools.path import resolve_path


def str_replace_editor(
    path: str, old_string: str, new_string: str, replace_all: bool = False
) -> dict:
    """
    Tool edit file bằng exact match string, không cần ghi đè toàn bộ file.
    """
    try:
        file_path = resolve_path(path)

        if not file_path.exists():
            return {"success": False, "path": path, "error": "FILE NOT FOUND"}

        file_content = file_path.read_text(encoding="utf-8")

        string_occurences = file_content.count(old_string)

        if string_occurences == 0:
            return {
                "success": False,
                "path": path,
                "error": "old string not found in file",
            }
        elif string_occurences == 1:
            file_content = file_content.replace(old_string, new_string)
        elif string_occurences > 1:
            if replace_all == True:
                file_content = file_content.replace(old_string, new_string)
            elif replace_all == False:
                return {
                    "success": False,
                    "path": path,
                    "error": "AMBIGUOS MATCH, use replace_all == True or make old_string more specific",
                }
        file_path.write_text(file_content, encoding="utf-8")
        return {
            "success": True,
            "path": path,
            "occurrences_replaced": string_occurences if replace_all else 1,
            "replace_all": replace_all,
        }

    except Exception as e:
        return {"success": False, "path": path, "error": str(e)}
