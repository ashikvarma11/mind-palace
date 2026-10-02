import hashlib
import os
from pathlib import Path
import tempfile
from .errors import WorkerError
from .paths import no_links


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    no_links(path)
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise WorkerError("VALIDATION_ERROR", "Stored file exceeds the supported bounds.")
    return digest(path.read_bytes())


def write(path, data, expected):
    no_links(path)
    if file_hash(path) != expected:
        raise WorkerError("CONFLICT", "A file changed; existing content was preserved.")
    path.parent.mkdir(parents=True, exist_ok=True)
    no_links(path.parent)
    handle, name = tempfile.mkstemp(prefix=".mp-", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if file_hash(path) != expected:
            raise WorkerError("CONFLICT", "A file changed; existing content was preserved.")
        os.replace(name, path)
    finally:
        temporary = Path(name)
        if temporary.exists():
            temporary.unlink()
