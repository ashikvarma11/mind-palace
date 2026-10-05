"""User-installed hook inbox. Reads only explicit transcript/memory scopes; no network."""
from __future__ import annotations

import argparse
import datetime
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import TypedDict

import portalocker

from .atomic_io import file_hash, write
from .chatgpt_sync import encoded, publish, sha, stored
from .errors import WorkerError
from .paths import no_links
from .session_capture import (MAX_EVENT, MAX_TRANSCRIPT, PROVIDERS, capture,
                              configuration, dedicated, fail, strict_json,
                              INBOX_QUOTA, write_failure_marker)

MAX_MEMORY = 65536
MAX_MEMORY_FILES = 1000
MAX_MEMORY_TOTAL = 4 * 1024 * 1024
MAX_INDEX_OBJECTS = 5000
MAX_INDEX_SCAN = 128 * 1024 * 1024
CHUNK_TARGET = 64 * 1024
HEX = re.compile(r"[0-9a-f]{64}", re.ASCII)
SPOOL_NAME = re.compile(r"[0-9a-f]{32}\.json", re.ASCII)
RETENTION_DAYS = 30


@dataclass(frozen=True)
class MemoryConsent:
    enabled: bool
    provider: str
    inbox: Path
    roots: tuple[Path, ...]


class IndexEntry(TypedDict):
    provider: str
    kind: str
    key: str
    sha256: str
    path: str
    bytes: int


def memory_consent(path: str | Path) -> MemoryConsent:
    target = dedicated(str(path))
    with target.open("rb") as stream:
        data = stream.read(MAX_EVENT + 1)
    if len(data) > MAX_EVENT:
        fail("LIMIT_EXCEEDED")
    value = strict_json(data)
    if not isinstance(value, dict) or set(value) != {"schema_version", "enabled", "provider", "inbox_root", "roots"}:
        fail("VALIDATION_ERROR")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or type(value["enabled"]) is not bool:
        fail("VALIDATION_ERROR")
    provider, roots = value["provider"], value["roots"]
    if not isinstance(provider, str) or provider not in PROVIDERS or not isinstance(roots, list) or not 0 <= len(roots) <= 32 or (value["enabled"] and not roots):
        fail("VALIDATION_ERROR")
    inbox = dedicated(value["inbox_root"])
    directories = tuple(dedicated(root) for root in roots)
    if len(set(directories)) != len(directories):
        fail("VALIDATION_ERROR")
    for root in directories:
        if root == inbox or root in inbox.parents or inbox in root.parents:
            fail("VALIDATION_ERROR")
        if any(root != other and (root in other.parents or other in root.parents) for other in directories):
            fail("VALIDATION_ERROR")
    return MemoryConsent(value["enabled"], provider, inbox, directories)


def snapshot_memory(config_path: str | Path, memory_path: str | Path) -> dict[str, int | str]:
    config, _, inbox = configuration(config_path)
    consent = memory_consent(memory_path)
    if not config["enabled"] or not consent.enabled:
        return {"status": "paused", "created": 0}
    if consent.provider != config["provider"] or consent.inbox != inbox:
        fail("VALIDATION_ERROR")
    objects: dict[Path, bytes] = {}
    total, unavailable, scanned = 0, 0, 0
    for root in consent.roots:
        if not root.exists():
            unavailable += 1
            continue
        if not root.is_dir():
            fail("VALIDATION_ERROR")
        for directory, dirs, files in os.walk(root, followlinks=False):
            parent = Path(directory)
            if len(parent.relative_to(root).parts) > 4:
                fail("LIMIT_EXCEEDED")
            for name in dirs + files:
                no_links(parent / name)
                scanned += 1
                if scanned > MAX_MEMORY_FILES:
                    fail("LIMIT_EXCEEDED")
            for name in files:
                path = parent / name
                if path.suffix.lower() != ".md":
                    continue
                if not stat.S_ISREG(path.stat().st_mode):
                    fail("VALIDATION_ERROR")
                with path.open("rb") as stream:
                    before = os.fstat(stream.fileno())
                    data = stream.read(MAX_MEMORY + 1)
                    after = os.fstat(stream.fileno())
                no_links(path)
                if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino) or (after.st_size, after.st_mtime_ns, after.st_ino) != (path.stat().st_size, path.stat().st_mtime_ns, path.stat().st_ino):
                    fail("BUSY")
                total += len(data)
                if len(data) > MAX_MEMORY or total > MAX_MEMORY_TOTAL:
                    fail("LIMIT_EXCEEDED")
                try:
                    text = data.decode("utf-8")
                except UnicodeError:
                    fail("VALIDATION_ERROR")
                relative = path.relative_to(root).as_posix()
                key = sha((consent.provider + "\0" + str(root) + "\0" + relative).encode())
                digest = sha(data)
                record = {"schema_version": 1, "provider": consent.provider, "kind": "memory_snapshot",
                          "memory_key": key, "sha256": digest, "bytes": len(data), "raw_text": text,
                          "source_root": str(root), "relative_path": relative,
                          "provenance": "local_assistant_memory", "review_status": "unreviewed",
                          "decisions_confirmed": False, "completeness": "selected_files_only"}
                target = inbox / consent.provider / "memory" / key / (digest + ".json")
                objects[target] = encoded(record)
    no_links(inbox)
    inbox.mkdir(parents=True, exist_ok=True)
    lock = inbox / "capture.lock"
    no_links(lock)
    with portalocker.Lock(str(lock), mode="a", timeout=1, check_interval=0.05):
        current, _, current_inbox = configuration(config_path)
        latest = memory_consent(memory_path)
        if not current["enabled"] or not latest.enabled:
            return {"status": "paused", "created": 0}
        if current != config or current_inbox != inbox or latest != consent:
            fail("CONFLICT")
        pending = [(path, data) for path, data in objects.items() if not stored(path, data)]
        for path, data in pending:
            publish(path, data)
    return {"status": "captured" if pending else "unavailable" if unavailable else "duplicate",
            "created": len(pending), "unavailable_roots": unavailable}


def validate_session(value: object, provider: str, key: str, digest: str) -> int:
    fields = {"schema_version", "provider", "session_id", "session_key", "sha256", "bytes", "captured_at", "normalized", "transcript"}
    if not isinstance(value, dict) or set(value) != fields or type(value.get("schema_version")) is not int or value.get("schema_version") != 1 or value.get("provider") != provider or value.get("normalized") is not False or value.get("session_key") != key or value.get("sha256") != digest:
        fail("VALIDATION_ERROR")
    captured = value.get("captured_at")
    if not isinstance(captured, str) or not 1 <= len(captured) <= 64:
        fail("VALIDATION_ERROR")
    session = value.get("session_id")
    if not isinstance(session, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session, re.ASCII) or sha((provider + "\0" + session).encode()) != key:
        fail("VALIDATION_ERROR")
    text = value.get("transcript")
    if not isinstance(text, str):
        fail("VALIDATION_ERROR")
    data = text.encode("utf-8")
    if type(value.get("bytes")) is not int or value["bytes"] != len(data) or len(data) > MAX_TRANSCRIPT or sha(data) != digest:
        fail("CONFLICT")
    return len(data)


def validate_jsonl(data: bytes) -> None:
    if not data or not data.endswith(b"\n"):
        fail("VALIDATION_ERROR")
    for line in data.splitlines():
        if not line or len(line) > MAX_TRANSCRIPT:
            fail("LIMIT_EXCEEDED")
        if not isinstance(strict_json(line), dict):
            fail("VALIDATION_ERROR")


def transcript_chunks(data: bytes) -> list[bytes]:
    """Split only after complete records; one large record remains indivisible."""
    validate_jsonl(data)
    result: list[bytes] = []
    pending = bytearray()
    for line in data.splitlines(keepends=True):
        if pending and len(pending) + len(line) > CHUNK_TARGET:
            result.append(bytes(pending))
            pending.clear()
        pending.extend(line)
        if len(pending) >= CHUNK_TARGET:
            result.append(bytes(pending))
            pending.clear()
    if pending:
        result.append(bytes(pending))
    return result


def read_session_snapshot(path: Path, provider: str, key: str) -> tuple[dict[str, object], bytes]:
    no_links(path)
    if not path.is_file() or not HEX.fullmatch(path.stem) or path.suffix != ".json":
        fail("VALIDATION_ERROR")
    with path.open("rb") as stream:
        raw = stream.read(MAX_TRANSCRIPT * 6 + MAX_EVENT + 1)
    if len(raw) > MAX_TRANSCRIPT * 6 + MAX_EVENT:
        fail("LIMIT_EXCEEDED")
    value = strict_json(raw)
    if not isinstance(value, dict):
        fail("VALIDATION_ERROR")
    if value.get("schema_version") == 1:
        validate_session(value, provider, key, path.stem)
        return value, str(value["transcript"]).encode("utf-8")
    fields = {"schema_version", "kind", "provider", "session_id", "session_key", "sha256", "bytes", "captured_at", "normalized", "chunk_target_bytes", "chunks"}
    if set(value) != fields or type(value.get("schema_version")) is not int or value.get("schema_version") != 2 or value.get("kind") != "session_manifest" or value.get("provider") != provider or value.get("session_key") != key or value.get("sha256") != path.stem or value.get("normalized") is not False or value.get("chunk_target_bytes") != CHUNK_TARGET:
        fail("VALIDATION_ERROR")
    session = value.get("session_id")
    captured = value.get("captured_at")
    chunks = value.get("chunks")
    if not isinstance(session, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session, re.ASCII) or sha((provider + "\0" + session).encode()) != key:
        fail("VALIDATION_ERROR")
    if not isinstance(captured, str) or not 1 <= len(captured) <= 64 or not isinstance(chunks, list) or not 1 <= len(chunks) <= 1024:
        fail("VALIDATION_ERROR")
    parts: list[bytes] = []
    total = 0
    inbox = path.parents[2]
    for chunk in chunks:
        if not isinstance(chunk, dict) or set(chunk) != {"sha256", "bytes"}:
            fail("VALIDATION_ERROR")
        digest, size = chunk.get("sha256"), chunk.get("bytes")
        if not isinstance(digest, str) or not HEX.fullmatch(digest) or type(size) is not int or not 1 <= size <= MAX_TRANSCRIPT:
            fail("VALIDATION_ERROR")
        target = inbox / "objects" / "chunks" / (digest + ".jsonl")
        no_links(target)
        if not target.is_file() or target.stat().st_size != size:
            fail("CONFLICT")
        with target.open("rb") as stream:
            part = stream.read(size + 1)
        if len(part) != size or sha(part) != digest:
            fail("CONFLICT")
        validate_jsonl(part)
        total += size
        if total > MAX_TRANSCRIPT:
            fail("LIMIT_EXCEEDED")
        parts.append(part)
    data = b"".join(parts)
    if type(value.get("bytes")) is not int or value["bytes"] != len(data) or sha(data) != path.stem:
        fail("CONFLICT")
    return value, data


def inspect_snapshot(path: Path, provider: str, kind: str, key: str) -> IndexEntry:
    no_links(path)
    if not path.is_file() or not HEX.fullmatch(path.stem) or path.suffix != ".json":
        fail("VALIDATION_ERROR")
    if kind == "session":
        _, data = read_session_snapshot(path, provider, key)
        size = len(data)
    else:
        with path.open("rb") as stream:
            raw = stream.read(MAX_TRANSCRIPT * 6 + MAX_EVENT + 1)
        if len(raw) > MAX_TRANSCRIPT * 6 + MAX_EVENT:
            fail("LIMIT_EXCEEDED")
        value = strict_json(raw)
        if not isinstance(value, dict) or type(value.get("schema_version")) is not int or value["schema_version"] != 1 or value.get("provider") != provider or value.get("sha256") != path.stem:
            fail("VALIDATION_ERROR")
        fields = {"schema_version", "provider", "kind", "memory_key", "sha256", "bytes", "raw_text", "source_root", "relative_path", "provenance", "review_status", "decisions_confirmed", "completeness"}
        if set(value) != fields or value.get("kind") != "memory_snapshot" or value.get("memory_key") != key or value.get("review_status") != "unreviewed" or value.get("decisions_confirmed") is not False or value.get("completeness") != "selected_files_only" or value.get("provenance") != "local_assistant_memory":
            fail("VALIDATION_ERROR")
        root, relative = value.get("source_root"), value.get("relative_path")
        if not isinstance(root, str) or not isinstance(relative, str) or sha((provider + "\0" + root + "\0" + relative).encode()) != key:
            fail("VALIDATION_ERROR")
        text = value.get("raw_text")
        if not isinstance(text, str):
            fail("VALIDATION_ERROR")
        data = text.encode("utf-8")
        if type(value.get("bytes")) is not int or value["bytes"] != len(data) or len(data) > MAX_MEMORY or sha(data) != path.stem:
            fail("CONFLICT")
        size = len(data)
    return {"provider": provider, "kind": kind, "key": key, "sha256": path.stem,
            "path": "", "bytes": size}


def drain_spool(inbox: Path) -> int:
    """Validate unique hook deliveries and publish canonical snapshot objects."""
    spool = inbox / "spool"
    no_links(spool)
    if not spool.exists():
        return 0
    if not spool.is_dir():
        fail("VALIDATION_ERROR")
    published = 0
    scanned = 0
    for provider_path in sorted(spool.iterdir(), key=lambda item: item.name):
        no_links(provider_path)
        if not provider_path.is_dir() or provider_path.name not in PROVIDERS:
            fail("VALIDATION_ERROR")
        provider = provider_path.name
        for path in sorted(provider_path.iterdir(), key=lambda item: item.name):
            no_links(path)
            scanned += 1
            if scanned > MAX_INDEX_OBJECTS:
                fail("LIMIT_EXCEEDED")
            if not path.is_file() or not SPOOL_NAME.fullmatch(path.name):
                fail("VALIDATION_ERROR")
            with path.open("rb") as stream:
                raw = stream.read(MAX_TRANSCRIPT * 6 + MAX_EVENT + 1)
            if len(raw) > MAX_TRANSCRIPT * 6 + MAX_EVENT:
                fail("LIMIT_EXCEEDED")
            value = strict_json(raw)
            if not isinstance(value, dict):
                fail("VALIDATION_ERROR")
            key, digest = value.get("session_key"), value.get("sha256")
            if not isinstance(key, str) or not HEX.fullmatch(key) or not isinstance(digest, str) or not HEX.fullmatch(digest):
                fail("VALIDATION_ERROR")
            validate_session(value, provider, key, digest)
            destination = inbox / provider / key / (digest + ".json")
            if destination.exists():
                inspect_snapshot(destination, provider, "session", key)
            else:
                data = str(value["transcript"]).encode("utf-8")
                descriptions: list[dict[str, object]] = []
                for part in transcript_chunks(data):
                    part_digest = sha(part)
                    chunk_path = inbox / "objects" / "chunks" / (part_digest + ".jsonl")
                    if not stored(chunk_path, part):
                        publish(chunk_path, part)
                    descriptions.append({"sha256": part_digest, "bytes": len(part)})
                manifest = {"schema_version": 2, "kind": "session_manifest",
                            "provider": provider, "session_id": value["session_id"],
                            "session_key": key, "sha256": digest, "bytes": len(data),
                            "captured_at": value["captured_at"], "normalized": False,
                            "chunk_target_bytes": CHUNK_TARGET, "chunks": descriptions}
                publish(destination, encoded(manifest))
                inspect_snapshot(destination, provider, "session", key)
                published += 1
            path.unlink()
    return published


def inbox_health(inbox: Path) -> dict[str, object]:
    total = failures = pending = scanned = 0
    if inbox.exists():
        for directory, dirs, files in os.walk(inbox, followlinks=False):
            parent = Path(directory)
            for name in dirs + files:
                no_links(parent / name)
                scanned += 1
                if scanned > MAX_INDEX_OBJECTS * 6:
                    fail("LIMIT_EXCEEDED")
            relative_parent = parent.relative_to(inbox).parts
            for name in files:
                path = parent / name
                if path == inbox / "health.json" or path == inbox / "capture.lock":
                    continue
                total += path.stat().st_size
                if total > INBOX_QUOTA:
                    fail("QUOTA_EXCEEDED")
                if relative_parent == ("failures",):
                    failures += 1
                if len(relative_parent) == 2 and relative_parent[0] == "spool":
                    pending += 1
    return {"schema_version": 1, "kind": "capture_health", "derived": True,
            "bytes_used": total, "quota_bytes": INBOX_QUOTA, "failures": failures,
            "pending_spool": pending, "retention_days": RETENTION_DAYS,
            "last_indexed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}


def read_health(inbox: Path) -> dict[str, object]:
    path = inbox / "health.json"
    no_links(path)
    if not path.exists():
        value = inbox_health(inbox)
        value["last_indexed_at"] = None
        return value
    with path.open("rb") as stream:
        raw = stream.read(MAX_EVENT + 1)
    value = strict_json(raw)
    fields = {"schema_version", "kind", "derived", "bytes_used", "quota_bytes", "failures", "pending_spool", "retention_days", "last_indexed_at"}
    if not isinstance(value, dict) or set(value) != fields or value.get("schema_version") != 1 or value.get("kind") != "capture_health" or value.get("derived") is not True or value.get("quota_bytes") != INBOX_QUOTA or value.get("retention_days") != RETENTION_DAYS:
        fail("VALIDATION_ERROR")
    for name in ("bytes_used", "failures", "pending_spool"):
        if type(value.get(name)) is not int or value[name] < 0:
            fail("VALIDATION_ERROR")
    if not isinstance(value.get("last_indexed_at"), str):
        fail("VALIDATION_ERROR")
    return value


def prune_redundant(config_path: str | Path) -> dict[str, int | bool]:
    """Remove only old prefixes whose complete bytes remain in a retained acknowledgment snapshot."""
    from .capture_recovery import instant
    import uuid
    _, _, inbox = configuration(config_path)
    if not inbox.exists():
        return {"removed_revisions": 0, "removed_chunks": 0, "bytes_freed": 0, "deferred": False}
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=RETENTION_DAYS)
    lock = inbox / "capture.lock"
    no_links(lock)
    with portalocker.Lock(str(lock), mode="a", timeout=1, check_interval=0.05):
        removals: list[tuple[Path, str, int]] = []
        removed_chunks: set[str] = set()
        retained_chunks: set[str] = set()
        scanned = loaded = 0
        for provider in sorted(PROVIDERS):
            root = inbox / provider
            no_links(root)
            if not root.exists():
                continue
            for folder in root.iterdir():
                no_links(folder)
                if folder.name == "memory":
                    continue
                if not folder.is_dir() or not HEX.fullmatch(folder.name):
                    fail("VALIDATION_ERROR")
                acknowledgment = inbox / "imported" / provider / (folder.name + ".json")
                no_links(acknowledgment)
                selected: bytes | None = None
                selected_hash: str | None = None
                if acknowledgment.exists():
                    with acknowledgment.open("rb") as stream:
                        raw = stream.read(MAX_EVENT + 1)
                    if len(raw) > MAX_EVENT:
                        fail("LIMIT_EXCEEDED")
                    ack = strict_json(raw)
                    fields = {"schema_version", "kind", "provider", "session_key", "session_id",
                              "selected_sha256", "canonical_session_id", "acknowledged_at"}
                    if (not isinstance(ack, dict) or set(ack) != fields or ack.get("schema_version") != 1
                            or ack.get("kind") != "vault_import" or ack.get("provider") != provider
                            or ack.get("session_key") != folder.name or not isinstance(ack.get("session_id"), str)
                            or sha((provider + "\0" + ack["session_id"]).encode()) != folder.name
                            or not isinstance(ack.get("selected_sha256"), str) or not HEX.fullmatch(ack["selected_sha256"])
                            or not isinstance(ack.get("canonical_session_id"), str)):
                        fail("VALIDATION_ERROR")
                    try:
                        if str(uuid.UUID(ack["canonical_session_id"])) != ack["canonical_session_id"]:
                            fail("VALIDATION_ERROR")
                    except ValueError:
                        fail("VALIDATION_ERROR")
                    instant(ack["acknowledged_at"])
                    selected_hash = ack["selected_sha256"]
                    _, selected = read_session_snapshot(folder / (selected_hash + ".json"), provider, folder.name)
                for path in folder.iterdir():
                    scanned += 1
                    if scanned > MAX_INDEX_OBJECTS:
                        fail("LIMIT_EXCEEDED")
                    metadata, data = read_session_snapshot(path, provider, folder.name)
                    loaded += len(data)
                    if loaded > MAX_INDEX_SCAN:
                        # No files have been deleted. Keep import available when
                        # validation exceeds this operation's bounded IO budget.
                        return {"removed_revisions": 0, "removed_chunks": 0, "bytes_freed": 0, "deferred": True}
                    chunks = {str(item["sha256"]) for item in metadata.get("chunks", [])}
                    if (selected is not None and path.stem != selected_hash and instant(metadata["captured_at"]) <= cutoff
                            and selected.startswith(data)):
                        digest = file_hash(path)
                        if digest is None:
                            fail("CONFLICT")
                        removals.append((path, digest, path.stat().st_size))
                        removed_chunks.update(chunks)
                    else:
                        retained_chunks.update(chunks)
        chunks_to_remove: list[tuple[Path, str, int]] = []
        for digest in sorted(removed_chunks - retained_chunks):
            path = inbox / "objects/chunks" / (digest + ".jsonl")
            no_links(path)
            if file_hash(path) != digest:
                fail("CONFLICT")
            chunks_to_remove.append((path, digest, path.stat().st_size))
        # All references and content are checked before the first deletion.
        for path, digest, _ in removals + chunks_to_remove:
            if inbox not in path.parents:
                fail("VALIDATION_ERROR")
            no_links(path)
            if file_hash(path) != digest:
                fail("CONFLICT")
        freed = 0
        for path, _, size in removals + chunks_to_remove:
            no_links(path)
            path.unlink()
            freed += size
        return {"removed_revisions": len(removals), "removed_chunks": len(chunks_to_remove), "bytes_freed": freed, "deferred": False}


def rebuild_index(config_path: str | Path, *, allow_paused: bool = False) -> dict[str, int | str]:
    """App-side/on-demand cache, deliberately outside hook deadlines and source scans."""
    config, _, inbox = configuration(config_path)
    if not config["enabled"] and not allow_paused:
        return {"status": "paused"}
    if not inbox.exists():
        return {"status": "empty", "sessions": 0, "memories": 0, "revisions": 0}
    lock = inbox / "capture.lock"
    no_links(lock)
    with portalocker.Lock(str(lock), mode="a", timeout=1, check_interval=0.05):
        current, _, current_inbox = configuration(config_path)
        if not current["enabled"] and not allow_paused:
            return {"status": "paused"}
        if current != config or current_inbox != inbox:
            fail("CONFLICT")
        drain_spool(inbox)
        entries: list[IndexEntry] = []
        total, scanned = 0, 0
        for provider in sorted(PROVIDERS):
            root = inbox / provider
            no_links(root)
            if not root.exists():
                continue
            for directory, dirs, files in os.walk(root, followlinks=False):
                parent = Path(directory)
                for name in dirs + files:
                    no_links(parent / name)
                    scanned += 1
                    if scanned > MAX_INDEX_OBJECTS * 3:
                        fail("LIMIT_EXCEEDED")
                for name in files:
                    parts = (parent / name).relative_to(root).parts
                    if len(parts) == 2 and HEX.fullmatch(parts[0]):
                        kind, key = "session", parts[0]
                    elif len(parts) == 3 and parts[0] == "memory" and HEX.fullmatch(parts[1]):
                        kind, key = "memory", parts[1]
                    else:
                        fail("VALIDATION_ERROR")
                    path = parent / name
                    total += path.stat().st_size
                    if total > MAX_INDEX_SCAN or len(entries) >= MAX_INDEX_OBJECTS:
                        fail("LIMIT_EXCEEDED")
                    entry = inspect_snapshot(path, provider, kind, key)
                    entry["path"] = path.relative_to(inbox).as_posix()
                    entries.append(entry)
        entries.sort(key=lambda entry: entry["path"])
        value = encoded({"schema_version": 1, "kind": "capture_index", "derived": True,
                         "entries": entries})
        if len(value) > 1024 * 1024:
            fail("LIMIT_EXCEEDED")
        lines = ["# Mind Palace capture inbox", "", "Generated index. Original snapshots are authoritative.",
                 "No revision is designated latest; captured memory is unreviewed.", ""]
        for entry in entries:
            lines.append("- " + entry["provider"] + " " + entry["kind"] + " " + entry["key"] +
                         " [" + entry["sha256"] + "](" + entry["path"] + ")")
        markdown = ("\n".join(lines) + "\n").encode()
        if len(markdown) > 1024 * 1024:
            fail("LIMIT_EXCEEDED")
        for name, data in (("index.json", value), ("index.md", markdown)):
            path = inbox / name
            previous = file_hash(path)
            if previous != sha(data):
                write(path, data, previous)
        health = encoded(inbox_health(inbox))
        health_path = inbox / "health.json"
        previous = file_hash(health_path)
        if previous != sha(health):
            write(health_path, health, previous)
    return {"status": "indexed", "sessions": len({(item["provider"], item["key"]) for item in entries if item["kind"] == "session"}),
            "memories": len({(item["provider"], item["key"]) for item in entries if item["kind"] == "memory"}),
            "revisions": len(entries)}


def run_hook(config_path: str | Path, event: object,
             memory_path: str | Path | None = None) -> dict[str, object]:
    # Keep the optional argument for old installed snippets. Memory scans now run
    # only during an explicit app-side index operation.
    return capture(config_path, event)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mind Palace local capture hook/inbox index")
    parser.add_argument("--config")
    parser.add_argument("--app-control-root")
    parser.add_argument("--memory-config")
    parser.add_argument("--rebuild-index", action="store_true")
    args = parser.parse_args()
    event = None
    try:
        if args.app_control_root:
            if args.config or args.memory_config or args.rebuild_index:
                fail("VALIDATION_ERROR")
            from .capture_control import dispatch
            # App control is one bounded JSONL frame. Do not require EOF:
            # unrelated inherited pipe handles must not delay dispatch.
            data = sys.stdin.buffer.readline(MAX_EVENT + 1)
            if len(data) > MAX_EVENT:
                fail("LIMIT_EXCEEDED")
            result = dispatch(args.app_control_root, strict_json(data), Path(sys.executable))
            sys.stdout.buffer.write(encoded(result) + b"\n")
            return 0
        if not args.config:
            fail("VALIDATION_ERROR")
        if args.rebuild_index:
            if args.memory_config is not None:
                snapshot_memory(args.config, args.memory_config)
            result = rebuild_index(args.config)
        else:
            data = sys.stdin.buffer.read(MAX_EVENT + 1)
            if len(data) > MAX_EVENT:
                fail("LIMIT_EXCEEDED")
            event = strict_json(data)
            result = run_hook(args.config, event, args.memory_config)
        # Never send captured content/instructions back through hook stdout.
        status = str(result["status"])
        memory_result = result.get("memory")
        if isinstance(memory_result, dict):
            status += "; memory=" + str(memory_result["status"])
        sys.stderr.write("Mind Palace inbox: " + status + "\n")
        return 0
    except portalocker.exceptions.LockException:
        code = "BUSY"
    except WorkerError as error:
        code = error.code
    except (OSError, TypeError, KeyError, ValueError, RecursionError, UnicodeError):
        code = "UNAVAILABLE"
    if args.config and not args.rebuild_index:
        write_failure_marker(args.config, event, code)
    sys.stderr.write("Mind Palace inbox: " + code + "\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
