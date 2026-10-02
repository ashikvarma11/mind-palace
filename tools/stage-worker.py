"""Prepare a fixed, ignored Windows worker resource tree; never launch it."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
EXE = "mind-palace-memory-worker.exe"
MANIFEST = "worker-manifest.json"
MAX_FILES = 512
MAX_ENTRIES = 2048
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024


def no_links(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or part.is_junction():
            raise ValueError("Redirected staging path rejected")


def safe_relative(name: str) -> str:
    if not name or "\\" in name or ":" in name or any(ord(c) < 32 for c in name):
        raise ValueError("Unsafe resource name")
    path = PurePosixPath(name)
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    if path.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError("Unsafe resource path")
    if len(path.parts) > 16:
        raise ValueError("Resource path depth exceeds bounds")
    for part in path.parts:
        if part.endswith((" ", ".")) or any(c in part for c in '<>"|?*') or part.split(".")[0].casefold() in reserved:
            raise ValueError("Unsafe Windows resource name")
    return name


def file_digest(path: Path, expected_size: int) -> str:
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        while chunk := stream.read(64 * 1024):
            count += len(chunk)
            if count > expected_size or count > MAX_FILE_BYTES:
                raise ValueError("Worker resource changed or exceeds bounds")
            digest.update(chunk)
    if count != expected_size:
        raise ValueError("Worker resource changed during inventory")
    return digest.hexdigest()


def inventory(root: Path, staged=False) -> dict:
    no_links(root)
    if not root.is_dir():
        raise ValueError("Frozen worker directory is unavailable")
    files = []
    seen = set()
    count = total = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        no_links(directory)
        with os.scandir(directory) as entries:
            for entry in entries:
                count += 1
                if count > MAX_ENTRIES:
                    raise ValueError("Resource entry count exceeds bounds")
                path = Path(entry.path)
                no_links(path)
                relative = safe_relative(path.relative_to(root).as_posix())
                if relative.casefold() in seen:
                    raise ValueError("Case-colliding resource entries rejected")
                seen.add(relative.casefold())
                if relative == MANIFEST:
                    if not staged or not entry.is_file(follow_symlinks=False):
                        raise ValueError("Unexpected resource manifest in build input")
                    continue
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    raise ValueError("Non-file resource rejected")
                # Windows DirEntry.stat reports st_nlink=0; Path.stat performs
                # the required OS query rather than relying on that cache.
                information = path.stat(follow_symlinks=False)
                if information.st_nlink != 1:
                    raise ValueError("Hard-linked worker resource rejected")
                size = information.st_size
                total += size
                if len(files) >= MAX_FILES or size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                    raise ValueError("Worker resource size exceeds bounds")
                digest = file_digest(path, size)
                # Detect concurrent input changes before approving this inventory.
                if path.stat().st_size != size:
                    raise ValueError("Worker resource changed during inventory")
                files.append({"path": relative, "bytes": size, "sha256": digest})
    files.sort(key=lambda item: item["path"])
    if not any(item["path"] == EXE and item["bytes"] > 0 for item in files):
        raise ValueError("Fixed worker executable is missing")
    return {"schema_version": 1, "platform": "windows-x86_64", "executable": EXE, "files": files}


def verify(root: Path) -> dict:
    path = root / MANIFEST
    no_links(path)
    if not path.is_file() or path.stat().st_size > 256 * 1024:
        raise ValueError("Worker manifest is missing or exceeds bounds")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate manifest property")
            result[key] = value
        return result
    expected = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Invalid JSON number")))
    actual = inventory(root, staged=True)
    # Canonical encoding also distinguishes bools from integer schema/size fields.
    if json.dumps(expected, sort_keys=True) != json.dumps(actual, sort_keys=True):
        raise ValueError("Staged worker inventory mismatch; existing files preserved")
    return actual


def owned(path: Path, root: Path) -> None:
    no_links(root)
    no_links(path)
    absolute_root = root.absolute()
    absolute_path = path.absolute()
    if absolute_path == absolute_root or not absolute_path.is_relative_to(absolute_root):
        raise ValueError("Staging target escapes project")
    if ".." in absolute_path.parts:
        raise ValueError("Unresolved staging target rejected")


def stage(root: Path, *, check=False, refresh=False) -> dict:
    root = root.absolute()
    source = root / ".tools/probe-dist/mind-palace-memory-worker"
    target = root / "src-tauri/resources/memory-worker"
    owned(source, root)
    owned(target, root)
    expected = inventory(source)
    if target.exists():
        current = verify(target)
        if current == expected:
            return current
        if check or not refresh:
            raise ValueError("Build input changed; explicitly refresh the verified generated bundle")
    elif check:
        raise ValueError("Worker is not staged")
    target.parent.mkdir(parents=True, exist_ok=True)
    owned(target.parent, root)
    temporary = Path(tempfile.mkdtemp(prefix=".worker-stage-", dir=target.parent))
    owned(temporary, root)
    for item in expected["files"]:
        relative = item["path"]
        origin, destination = source / relative, temporary / relative
        owned(origin, root)
        owned(destination, root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, destination)
    # Generated inventory is deliberately not source-controlled.
    (temporary / MANIFEST).write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    if verify(temporary) != expected:
        raise ValueError("Copied worker differs from build input")
    if target.exists():
        # Recheck before a recoverable move. Never move an unverified directory.
        if verify(target) != current:
            raise ValueError("Staged bundle changed during refresh")
        backup = root / ".tools/worker-stage-backups" / str(uuid.uuid4())
        owned(backup, root)
        backup.parent.mkdir(parents=True, exist_ok=True)
        owned(target, root)
        owned(backup, root)
        target.rename(backup)
    owned(target, root)
    temporary.rename(target)
    return verify(target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--check", action="store_true")
    options.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    result = stage(ROOT, check=args.check, refresh=args.refresh)
    print(json.dumps({"files": len(result["files"]), "bytes": sum(item["bytes"] for item in result["files"]),
                      "checked": args.check, "executable": result["executable"]}))


if __name__ == "__main__":
    main()
