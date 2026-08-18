from pathlib import Path

ROOTDIR = Path(__file__).parent.parent.parent.resolve()
WORKSPACE = (ROOTDIR / "workspace").resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)


VENVSCRIPTS = ROOTDIR / "venv" / "Scripts"

BASHPATH = r"D:\git\Git\bin\bash.exe"


def resolve_path(path: str) -> Path:
    """
    Chuẩn hóa đường dẫn về thành workspace/
    """
    path_object = Path(path)
    path_parts = path_object.parts

    if path_parts and path_parts[0].lower() in {"workspace", ".workspace"}:
        path_object = Path(*path_parts[1:])

    full_path = (WORKSPACE / path_object).resolve()

    if not str(full_path).startswith(str(WORKSPACE)):
        raise ValueError("Lỗi đường dẫn không nằm trong workspace/ ")

    return full_path
