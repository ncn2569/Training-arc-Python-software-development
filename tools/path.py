from pathlib import Path

WORKSPACE = Path("./workspace").resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)


ROOT_DIR = Path(__file__).parent.parent.resolve()
VENV_SCRIPTS = ROOT_DIR / "venv" / "Scripts"

BASH_PATH = r"D:\git\Git\bin\bash.exe"


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
