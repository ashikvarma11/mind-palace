"""Scoped Codex recovery and explicit history import; source files stay read-only."""
from __future__ import annotations

import datetime
import os
from pathlib import Path
import re
from typing import TypedDict
import uuid

from .atomic_io import file_hash, write
from .capture_inbox import HEX, MAX_INDEX_OBJECTS, read_session_snapshot
from .chatgpt_sync import encoded, sha
from .errors import WorkerError
from .paths import no_links
from .session_capture import MAX_LINE, MAX_TRANSCRIPT, capture, configuration, fail, read_transcript, strict_json

MAX_SCAN = 128 * 1024 * 1024
HISTORY_PAGE = 10
SESSION_ID = re.compile(r"[A-Za-z0-9_-]{1,128}", re.ASCII)


class Rollout(TypedDict):
    relative_path: str
    session_id: str
    bytes: int
    mtime_ns: int
    header_sha256: str
    started_at: str | None


def instant(value: object) -> datetime.datetime:
    if not isinstance(value, str) or len(value) > 64:
        fail("VALIDATION_ERROR")
    try:
        result = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None or result.utcoffset() != datetime.timedelta(0):
            fail("VALIDATION_ERROR")
        return result
    except ValueError:
        fail("VALIDATION_ERROR")
    raise AssertionError("unreachable")


def rollout_header(path: Path, source: Path) -> Rollout | None:
    no_links(path)
    before = path.stat()
    if not path.is_file() or not 0 < before.st_size <= MAX_TRANSCRIPT:
        fail("LIMIT_EXCEEDED")
    with path.open("rb") as stream:
        raw = stream.readline(MAX_LINE + 1)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        fail("BUSY")
    if len(raw) > MAX_LINE or not raw.endswith(b"\n"):
        fail("VALIDATION_ERROR")
    value = strict_json(raw)
    if not isinstance(value, dict) or value.get("type") != "session_meta":
        return None
    payload = value.get("payload")
    if not isinstance(payload, dict) or not isinstance(payload.get("id"), str) or not SESSION_ID.fullmatch(payload["id"]):
        fail("VALIDATION_ERROR")
    timestamp = payload.get("timestamp", value.get("timestamp"))
    started = None if timestamp is None else instant(timestamp).isoformat().replace("+00:00", "Z")
    return {"relative_path": path.relative_to(source).as_posix(), "session_id": payload["id"],
            "bytes": before.st_size, "mtime_ns": before.st_mtime_ns, "header_sha256": sha(raw), "started_at": started}


def scan(source: Path, known: set[str] | None = None) -> tuple[list[Rollout], int]:
    candidates: list[Rollout] = []
    skipped = scanned = 0
    for directory, dirs, files in os.walk(source, followlinks=False):
        parent = Path(directory)
        no_links(parent)
        if len(parent.relative_to(source).parts) > 8:
            fail("LIMIT_EXCEEDED")
        for name in dirs + files:
            no_links(parent / name)
            scanned += 1
            if scanned > MAX_INDEX_OBJECTS * 3:
                fail("LIMIT_EXCEEDED")
        for name in sorted(files):
            path = parent / name
            if path.suffix != ".jsonl":
                continue
            try:
                item = rollout_header(path, source)
                if item is not None and (known is None or item["session_id"] in known):
                    candidates.append(item)
            except (WorkerError, OSError):
                skipped += 1
            if len(candidates) > 1000:
                fail("LIMIT_EXCEEDED")
    candidates.sort(key=lambda item: item["relative_path"])
    return candidates, skipped


def recover_known(config_path: Path) -> dict[str, object]:
    config, source, inbox = configuration(config_path)
    if not config["enabled"]:
        return {"restored": 0, "unchanged": 0, "skipped": 0}
    known: dict[str, set[str]] = {}
    root = inbox / "codex"
    no_links(root)
    if root.exists():
        for folder in root.iterdir():
            no_links(folder)
            if folder.name == "memory":
                continue
            if not folder.is_dir() or not HEX.fullmatch(folder.name):
                fail("VALIDATION_ERROR")
            for path in folder.iterdir():
                metadata, _ = read_session_snapshot(path, "codex", folder.name)
                known.setdefault(str(metadata["session_id"]), set()).add(path.stem)
    if not known:
        return {"restored": 0, "unchanged": 0, "skipped": 0}
    candidates, skipped = scan(source, set(known))
    restored = unchanged = total = 0
    for item in candidates:
        if total + item["bytes"] > MAX_SCAN:
            skipped += 1
            continue
        total += item["bytes"]
        try:
            path = source / item["relative_path"]
            data, _ = read_transcript(str(path), source)
            if sha(data) in known[item["session_id"]]:
                unchanged += 1
                continue
            result = capture(config_path, {"hook_event_name": "Stop", "session_id": item["session_id"],
                                           "transcript_path": str(path)})
            if result["status"] == "captured":
                restored += 1
        except (WorkerError, OSError):
            skipped += 1
    return {"restored": restored, "unchanged": unchanged, "skipped": skipped}


def history_preview(root: Path, config_path: Path) -> dict[str, object]:
    _, source, _ = configuration(config_path)
    candidates, skipped = scan(source)
    preview_id = str(uuid.uuid4())
    created = datetime.datetime.now(datetime.timezone.utc)
    value = {"schema_version": 1, "kind": "codex_history_preview", "preview_id": preview_id,
             "source_revision": file_hash(config_path), "created_at": created.isoformat(),
             "candidates": candidates, "skipped": skipped}
    raw = encoded(value)
    if len(raw) > 1024 * 1024:
        fail("LIMIT_EXCEEDED")
    write(root / "settings/history-previews" / (preview_id + ".json"), raw, None)
    dates = sorted(item["started_at"] for item in candidates if item["started_at"] is not None)
    return {"preview_id": preview_id, "source_root": str(source),
            "sessions": len({item["session_id"] for item in candidates}), "files": len(candidates),
            "bytes": sum(item["bytes"] for item in candidates), "skipped": skipped,
            "earliest": dates[0] if dates else None, "latest": dates[-1] if dates else None}


def history_import(root: Path, config_path: Path, preview_id: str, offset: int) -> dict[str, object]:
    _, source, inbox = configuration(config_path)
    target = root / "settings/history-previews" / (preview_id + ".json")
    no_links(target)
    with target.open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        fail("LIMIT_EXCEEDED")
    preview = strict_json(raw)
    fields = {"schema_version", "kind", "preview_id", "source_revision", "created_at", "candidates", "skipped"}
    if (not isinstance(preview, dict) or set(preview) != fields or preview.get("schema_version") != 1
            or preview.get("kind") != "codex_history_preview" or preview.get("preview_id") != preview_id
            or preview.get("source_revision") != file_hash(config_path)):
        fail("CONFLICT")
    age = datetime.datetime.now(datetime.timezone.utc) - instant(preview["created_at"])
    if not datetime.timedelta(0) <= age <= datetime.timedelta(minutes=15):
        fail("CONFLICT")
    candidates = preview["candidates"]
    if not isinstance(candidates, list) or len(candidates) > 1000 or offset > len(candidates):
        fail("VALIDATION_ERROR")
    created = skipped = total = 0
    next_offset = offset
    # Explicit history confirmation can import a paused scope. Source consent is
    # never edited: publish the same immutable delivery format directly instead.
    import tempfile
    for item in candidates[offset:offset + HISTORY_PAGE]:
        if (not isinstance(item, dict) or set(item) != {"relative_path", "session_id", "bytes", "mtime_ns", "header_sha256", "started_at"}
                or not isinstance(item["relative_path"], str) or Path(item["relative_path"]).is_absolute()
                or Path(item["relative_path"]).drive
                or ".." in Path(item["relative_path"]).parts or not isinstance(item["session_id"], str)
                or not SESSION_ID.fullmatch(item["session_id"]) or type(item["bytes"]) is not int
                or not 0 < item["bytes"] <= MAX_TRANSCRIPT or type(item["mtime_ns"]) is not int
                or not isinstance(item["header_sha256"], str) or not HEX.fullmatch(item["header_sha256"])
                or (item["started_at"] is not None and not isinstance(item["started_at"], str))):
            fail("VALIDATION_ERROR")
        if total + item["bytes"] > MAX_SCAN:
            break
        total += item["bytes"]
        next_offset += 1
        path = source / item["relative_path"]
        try:
            if file_hash(config_path) != preview["source_revision"]:
                fail("CONFLICT")
            if rollout_header(path, source) != item:
                raise WorkerError("CONFLICT", "History source changed.")
            data, partial = read_transcript(str(path), source)
            if not data or partial:
                raise WorkerError("BUSY", "History source is incomplete.")
            if rollout_header(path, source) != item or file_hash(config_path) != preview["source_revision"]:
                raise WorkerError("CONFLICT", "History source or consent changed.")
            digest = sha(data)
            from .session_capture import INBOX_QUOTA, FAILURE_RESERVE, quota_usage
            record = {"schema_version": 1, "provider": "codex", "session_id": item["session_id"],
                      "session_key": sha(("codex\0" + item["session_id"]).encode()), "sha256": digest,
                      "bytes": len(data), "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      "normalized": False, "transcript": data.decode("utf-8")}
            delivery = encoded(record)
            if quota_usage(inbox) + len(delivery) > INBOX_QUOTA - FAILURE_RESERVE:
                raise WorkerError("QUOTA_EXCEEDED", "Capture inbox is full.")
            directory = inbox / "spool/codex"
            no_links(directory)
            directory.mkdir(parents=True, exist_ok=True)
            destination = directory / (uuid.uuid4().hex + ".json")
            handle, temporary = tempfile.mkstemp(prefix=".capture-", dir=directory)
            try:
                with os.fdopen(handle, "wb") as stream:
                    stream.write(delivery)
                    stream.flush()
                    os.fsync(stream.fileno())
                if rollout_header(path, source) != item or file_hash(config_path) != preview["source_revision"]:
                    raise WorkerError("CONFLICT", "History source or consent changed.")
                os.rename(temporary, destination) if os.name == "nt" else os.link(temporary, destination)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            created += 1
        except (WorkerError, OSError):
            skipped += 1
    return {"captured": created, "skipped": skipped,
            "next_offset": next_offset if next_offset < len(candidates) else None}
