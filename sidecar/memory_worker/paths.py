from pathlib import Path
import os
import re
from .errors import WorkerError

ID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
OWNED = re.compile(rf"(?:sessions/{ID}\.md|records/{ID}\.json|events/{ID}\.jsonl|sources/{ID}/(?:original\.txt|source\.json|revisions/[0-9a-f]{{64}}\.txt)|imports/(?:claude-code|codex)/[0-9a-f]{{64}}\.json)")


def filesystem_path(value: str | Path) -> Path:
    """Extended absolute Windows paths; no registry or global configuration change."""
    text = str(value)
    if os.name != "nt" or text.startswith("\\\\?\\"):
        return Path(text)
    if not Path(value).is_absolute() or ".." in Path(value).parts:
        raise WorkerError("VALIDATION_ERROR", "Absolute paths are required.")
    if text.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + text[2:])
    return Path("\\\\?\\" + text.replace("/", "\\"))


def no_links(path):
    for part in [path, *path.parents]:
        if part.is_symlink() or part.is_junction():
            raise WorkerError("VALIDATION_ERROR", "Linked filesystem paths are unavailable.")


def root_path(value):
    if ".." in Path(value).parts:
        raise WorkerError("VALIDATION_ERROR", "Select a dedicated vault directory.")
    path = Path(value).absolute()
    no_links(path)
    if path == Path(path.anchor) or len(path.parts) < 3:
        raise WorkerError("VALIDATION_ERROR", "Select a dedicated vault directory.")
    return path


def owned_path(root, relative):
    if not isinstance(relative, str) or not OWNED.fullmatch(relative):
        raise WorkerError("VALIDATION_ERROR", "Invalid vault record path.")
    path = root / relative
    no_links(path)
    return path
