# """
# Normal function
# """

# import datetime
# import time
# from pathlib import Path

# WORKSPACE = Path("./workspace").resolve()


# def resolve_workspace_path(input_path: str) -> Path:
#     """Chuẩn hóa đường dẫn -> workspace/*"""
#     path_obj = Path(input_path)
#     parts = path_obj.parts
#     if parts and parts[0].lower() in {"workspace", ".workspace"}:
#         path_obj = Path(*parts[1:])
#     full_path = (WORKSPACE / path_obj).resolve()
#     if not str(full_path).startswith(str(WORKSPACE)):
#         raise ValueError(f"Access denied: Path '{input_path}' is outside workspace.")
#     return full_path


# def read_file(path: str) -> dict:
#     try:
#         target_path = resolve_workspace_path(path)
#         content = target_path.read_text(encoding="utf-8")
#         rel_path = target_path.relative_to(WORKSPACE)
#         result = {
#             "success": True,
#             "path": str(rel_path).replace("\\", "/"),
#             "content": content,
#             "size": len(content.encode("utf-8")),
#         }
#         return result
#     except Exception as e:
#         return {"success": False, "path": path, "error": str(e)}


# def write_file(path: str, content: str) -> dict:
#     try:
#         target_path = resolve_workspace_path(path)

#         existed = target_path.exists()
#         action = "overwritten" if existed else "created"

#         target_path.parent.mkdir(parents=True, exist_ok=True)

#         target_path.write_text(data=content, encoding="utf-8")
#         bytes_written = len(content.encode("utf-8"))

#         rel_path = target_path.relative_to(WORKSPACE)

#         return {
#             "success": True,
#             "path": str(rel_path).replace("\\", "/"),
#             "bytes_written": bytes_written,
#             "action": action,
#         }

#     except Exception as e:
#         return {"success": False, "path": path, "error": str(e)}


# def read_time() -> dict:
#     return {
#         "success": True,
#         "content": datetime.datetime.fromtimestamp(time.time()).isoformat(),
#     }
