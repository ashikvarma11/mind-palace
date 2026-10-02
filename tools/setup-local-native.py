"""Explicit developer-only download/inspection; never runs an installer."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".tools" / "native"
MAX_DOWNLOAD = 512 * 1024 * 1024
MAX_EXPANDED = 2 * 1024 * 1024 * 1024


def safe_name(name: str) -> PurePosixPath:
    if not name or "\\" in name or ":" in name or any(ord(c) < 32 for c in name):
        raise ValueError("Unsafe archive name")
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in ("..", ".") for p in name.split("/")):
        raise ValueError("Unsafe archive path")
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
                *(f"lpt{i}" for i in range(1, 10))}
    for part in path.parts:
        if part.endswith((" ", ".")) or any(c in part for c in '<>"|?*') or part.split(".")[0].casefold() in reserved:
            raise ValueError("Unsafe Windows archive name")
    return path


def check_owned(path: Path) -> None:
    if not path.is_relative_to(BASE):
        raise ValueError("Tool path escapes project tooling")
    for parent in (path, *path.parents):
        if parent.exists() and (parent.is_symlink() or parent.is_junction()):
            raise ValueError("Redirected tool path rejected")
        if parent == ROOT:
            break


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(item: dict) -> Path:
    url = urllib.parse.urlparse(item["url"])
    if url.scheme != "https" or url.hostname not in (
        "static.rust-lang.org", "download.visualstudio.microsoft.com"
    ):
        raise ValueError("Unexpected artifact host")
    cache = BASE / "cache"
    check_owned(cache)
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / Path(url.path).name
    check_owned(target)
    if target.exists():
        if target.is_symlink() or digest(target) != item["sha256"]:
            raise ValueError("Cached artifact hash mismatch")
        return target
    part = target.with_suffix(target.suffix + ".partial")
    check_owned(part)
    with urllib.request.urlopen(item["url"], timeout=60) as response:
        final = urllib.parse.urlparse(response.url)
        if final.scheme != "https" or final.hostname != url.hostname:
            raise ValueError("Unexpected artifact redirect")
        count = 0
        with part.open("xb") as out:
            while chunk := response.read(1024 * 1024):
                count += len(chunk)
                if count > MAX_DOWNLOAD:
                    raise ValueError("Download limit exceeded")
                out.write(chunk)
    if digest(part) != item["sha256"]:
        raise ValueError("Downloaded artifact hash mismatch")
    part.rename(target)
    return target


def unpack(archive: Path, kind: str, destination: Path, inspect: bool) -> list[str]:
    # Validate every member before writing any file. No symlinks, executables
    # are not run here; metadata and licenses are preserved in raw extraction.
    entries = []
    total = 0
    seen = set()
    with (zipfile.ZipFile(archive) if kind == "zip" else tarfile.open(archive)) as pack:
        members = pack.infolist() if kind == "zip" else pack.getmembers()
        for member in members:
            name = member.filename if kind == "zip" else member.name
            path = safe_name(name.rstrip("/"))
            key = str(path).casefold()
            if key in seen:
                raise ValueError("Duplicate archive path")
            seen.add(key)
            directory = member.is_dir() if kind == "zip" else member.isdir()
            if kind == "zip":
                mode = member.external_attr >> 16
                if (mode & 0o170000) == 0o120000:
                    raise ValueError("Archive symlink rejected")
                size = member.file_size
            else:
                if not (member.isfile() or directory):
                    raise ValueError("Archive special member rejected")
                size = member.size
            total += size
            if size > MAX_DOWNLOAD or total > MAX_EXPANDED or len(seen) > 100000:
                raise ValueError("Expanded archive limit exceeded")
            entries.append((member, path, directory))
        if not inspect:
            if destination.is_relative_to(BASE):
                check_owned(destination)
            if destination.exists():
                raise ValueError("Extraction target already exists")
            destination.mkdir(parents=True)
            for member, path, directory in entries:
                target = destination.joinpath(*path.parts)
                if directory:
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = pack.open(member) if kind == "zip" else pack.extractfile(member)
                    with source, target.open("xb") as out:
                        while chunk := source.read(1024 * 1024):
                            out.write(chunk)
    return [str(entry[1]) for entry in entries]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--only", choices=("msvc-dynamic-crt",))
    args = parser.parse_args()
    # Reject pre-existing redirected parents before any writes.
    for path in (ROOT / ".tools", BASE):
        if path.exists() and (path.is_symlink() or path.is_junction()):
            raise ValueError("Redirected tooling root rejected")
    config = json.loads((ROOT / "config/native-toolchain.json").read_text())
    for item in config["artifacts"]:
        if args.only and item["name"] != args.only:
            continue
        artifact = download(item)
        dest = BASE / "raw" / item["name"]
        names = unpack(artifact, item["kind"], dest, not args.extract)
        print(json.dumps({"name": item["name"], "bytes": artifact.stat().st_size,
                          "verified": True, "members": len(names), "sample": names[:12]},
                         ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
