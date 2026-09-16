from pathlib import Path


def archive_target(root, member):
    root = Path(root)
    candidate = root / member
    if str(candidate).startswith(str(root)):
        return candidate
    raise ValueError("unsafe archive member")
