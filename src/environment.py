from pathlib import Path


def resolve_directory(value, base):
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()
