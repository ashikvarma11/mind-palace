"""Local export-to-inbox sync. No account access, network, inference or vault writes."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import BinaryIO, TypedDict, cast
import zipfile

import portalocker

from .errors import WorkerError
from .paths import no_links, filesystem_path
from .session_capture import dedicated, strict_json

type Json = None | bool | int | float | str | list[Json] | dict[str, Json]
MAX_JSON = 64 * 1024 * 1024
MAX_ARCHIVE = 512 * 1024 * 1024
MAX_REVISION = 20 * 1024 * 1024
MAX_MEMORY = 256 * 1024
MAX_CONVERSATIONS = 10000
MAX_NODES = 10000
MAX_FILES = 50000
INBOX_QUOTA = 512 * 1024 * 1024
HISTORY_NAME = re.compile(r"conversations(?:-\d+)?\.json", re.ASCII)
IDENTITY = re.compile(r"[A-Za-z0-9_-]{1,128}", re.ASCII)
HEX = re.compile(r"[0-9a-f]{64}", re.ASCII)


def fail(code: str = "VALIDATION_ERROR") -> None:
    raise WorkerError(code, "Local ChatGPT sync could not complete.")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class Consent:
    enabled: bool
    profile: str
    source: Path
    inbox: Path
    excluded: frozenset[str]


class SyncResult(TypedDict):
    status: str
    conversations: int
    memory_snapshots: int
    created: int
    duplicates: int
    excluded: int
    warnings: dict[str, int]


class Message(TypedDict):
    node_id: str
    message_id: str
    role: str
    text_parts: list[str]
    created_at: Json
    source_pointer: str


class Normalized(TypedDict):
    messages: list[Message]
    parents: dict[str, str | None]
    active_path: list[str]
    warnings: dict[str, int]
    review_status: str
    decisions_confirmed: bool


def configuration(path: str | Path) -> Consent:
    target = filesystem_path(dedicated(str(path)))
    no_links(target)
    with target.open("rb") as stream:
        data = stream.read(65537)
    if len(data) > 65536:
        fail("LIMIT_EXCEEDED")
    config = strict_json(data)
    fields = {"schema_version", "enabled", "profile", "source_root", "inbox_root", "excluded_conversation_ids"}
    if not isinstance(config, dict) or set(config) != fields:
        fail()
    if type(config["schema_version"]) is not int or config["schema_version"] != 1 or type(config["enabled"]) is not bool:
        fail()
    profile, exclusions = config["profile"], config["excluded_conversation_ids"]
    if not isinstance(profile, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", profile, re.ASCII):
        fail()
    if not isinstance(exclusions, list) or len(exclusions) > MAX_CONVERSATIONS:
        fail()
    if any(not isinstance(item, str) or not IDENTITY.fullmatch(item) for item in exclusions):
        fail()
    if len(set(exclusions)) != len(exclusions):
        fail()
    source, inbox = filesystem_path(dedicated(config["source_root"])), filesystem_path(dedicated(config["inbox_root"]))
    if not source.is_dir() or source == inbox or source in inbox.parents or inbox in source.parents:
        fail()
    return Consent(config["enabled"], profile, source, inbox, frozenset(exclusions))


def selected_file(value: str | Path, source: Path) -> Path:
    path = filesystem_path(dedicated(str(value)))
    if source not in path.parents or not stat.S_ISREG(path.stat().st_mode):
        fail()
    return path


def fingerprint(info: os.stat_result) -> tuple[int, int, int]:
    return info.st_size, info.st_mtime_ns, info.st_ino


def unchanged(stream: BinaryIO, path: Path, before: os.stat_result) -> None:
    no_links(path)
    if fingerprint(before) != fingerprint(os.fstat(stream.fileno())) or fingerprint(before) != fingerprint(path.stat()):
        fail("BUSY")


def read_history(value: str | Path, source: Path) -> list[tuple[str, bytes]]:
    path = selected_file(value, source)
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_ARCHIVE:
            fail("LIMIT_EXCEEDED")
        if path.suffix.lower() == ".zip":
            parts: list[tuple[str, bytes]] = []
            with zipfile.ZipFile(stream) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_CONVERSATIONS:
                    fail("LIMIT_EXCEEDED")
                names: set[str] = set()
                total = 0
                for entry in entries:
                    name = entry.filename
                    # Never extract paths. Reject ambiguous history paths rather than
                    # silently accepting a ZIP that only partly matches this contract.
                    if HISTORY_NAME.fullmatch(Path(name.replace("\\", "/")).name) and not HISTORY_NAME.fullmatch(name):
                        fail("UNSUPPORTED_FORMAT")
                    if not HISTORY_NAME.fullmatch(name):
                        continue  # Account metadata, attachments and HTML aren't imported.
                    mode = entry.external_attr >> 16
                    if name in names or entry.flag_bits & 1 or stat.S_ISLNK(mode):
                        fail()
                    names.add(name)
                    total += entry.file_size
                    if len(names) > 100 or total > MAX_JSON or entry.file_size > MAX_JSON:
                        fail("LIMIT_EXCEEDED")
                    if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                        fail("UNSUPPORTED_FORMAT")
                    if entry.file_size > max(entry.compress_size, 1) * 500:
                        fail("LIMIT_EXCEEDED")
                    with archive.open(entry) as member:
                        data = member.read(MAX_JSON + 1)
                    if len(data) > MAX_JSON or len(data) != entry.file_size:
                        fail("LIMIT_EXCEEDED")
                    parts.append((name, data))
            if not parts:
                fail("UNSUPPORTED_FORMAT")
        elif HISTORY_NAME.fullmatch(path.name):
            data = stream.read(MAX_JSON + 1)
            if len(data) > MAX_JSON:
                fail("LIMIT_EXCEEDED")
            parts = [(path.name, data)]
        else:
            fail("UNSUPPORTED_FORMAT")
        unchanged(stream, path, before)
    return sorted(parts)


def fragments(data: bytes) -> list[bytes]:
    """Preserve each array item's exact UTF-8 bytes, without retaining excluded items."""
    try:
        text = data.decode("utf-8")
        decoder = json.JSONDecoder()
        cursor = 0
        def whitespace(index: int) -> int:
            while index < len(text) and text[index] in " \t\r\n":
                index += 1
            return index
        cursor = whitespace(cursor)
        if text[cursor:cursor + 1] != "[":
            fail("UNSUPPORTED_FORMAT")
        cursor = whitespace(cursor + 1)
        result: list[bytes] = []
        if text[cursor:cursor + 1] != "]":
            while True:
                _, end = decoder.raw_decode(text, cursor)
                raw = text[cursor:end].encode("utf-8")
                if len(raw) > MAX_REVISION or len(result) >= MAX_CONVERSATIONS:
                    fail("LIMIT_EXCEEDED")
                result.append(raw)
                cursor = whitespace(end)
                if text[cursor:cursor + 1] == "]":
                    break
                if text[cursor:cursor + 1] != ",":
                    fail()
                cursor = whitespace(cursor + 1)
        if text[cursor:cursor + 1] != "]" or whitespace(cursor + 1) != len(text):
            fail()
        return result
    except (ValueError, UnicodeError, RecursionError):
        fail()


def identity(value: object) -> str:
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        fail()
    return value


def number(value: Json) -> Json:
    if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
        fail()
    return value


def normalize(conversation: dict[str, Json]) -> Normalized:
    mapping = conversation.get("mapping")
    if not isinstance(mapping, dict) or not mapping:
        fail("UNSUPPORTED_FORMAT")
    if len(mapping) > MAX_NODES:
        fail("LIMIT_EXCEEDED")
    parents: dict[str, str | None] = {}
    warnings: dict[str, int] = {}
    def warn(code: str) -> None:
        warnings[code] = warnings.get(code, 0) + 1
    for key, node in mapping.items():
        identity(key)
        if not isinstance(node, dict) or node.get("id") != key:
            fail()
        parent = node.get("parent")
        if parent is not None and (not isinstance(parent, str) or parent not in mapping):
            fail()
        parents[key] = parent
    # Validate every branch in linear time, including branches outside current_node.
    done: set[str] = set()
    for key in parents:
        trail: set[str] = set()
        cursor: str | None = key
        while cursor is not None and cursor not in done:
            if cursor in trail:
                fail()
            trail.add(cursor)
            cursor = parents[cursor]
        done.update(trail)
    current = conversation.get("current_node")
    if current is not None and (not isinstance(current, str) or current not in mapping):
        fail()
    active: list[str] = []
    cursor = cast(str | None, current)
    while isinstance(cursor, str):
        active.append(cursor)
        cursor = parents[cursor]
    active.reverse()
    if current is None:
        warn("ACTIVE_BRANCH_UNAVAILABLE")
    messages: list[Message] = []
    for key, node in mapping.items():
        assert isinstance(node, dict)
        message = node.get("message")
        if message is None:
            continue
        if not isinstance(message, dict) or not isinstance(message.get("author"), dict):
            fail()
        author = message["author"]
        assert isinstance(author, dict)
        role = author.get("role")
        metadata = message.get("metadata", {})
        if not isinstance(metadata, dict):
            fail()
        if role not in ("user", "assistant") or metadata.get("is_visually_hidden_from_conversation") is True or metadata.get("is_thinking_preamble_message") is True:
            warn("NON_VISIBLE_MESSAGE")
            continue
        channel, recipient = message.get("channel"), message.get("recipient", "all")
        if channel not in (None, "final") or recipient != "all":
            warn("NON_VISIBLE_MESSAGE")
            continue
        content = message.get("content")
        if not isinstance(content, dict):
            fail()
        content_type = content.get("content_type")
        parts = content.get("parts")
        if content_type not in ("text", "multimodal_text"):
            warn("UNSUPPORTED_CONTENT")
            continue
        if not isinstance(parts, list):
            fail()
        text_parts: list[str] = []
        for part in parts:
            if isinstance(part, str):
                text_parts.append(part)
            elif content_type == "multimodal_text" and isinstance(part, dict):
                warn("UNSUPPORTED_ATTACHMENT")
            else:
                fail()
        messages.append({"node_id": key, "message_id": identity(message.get("id")),
                         "role": cast(str, role), "text_parts": text_parts,
                         "created_at": number(message.get("create_time")),
                         "source_pointer": "/mapping/" + key + "/message"})
    return {"messages": messages, "parents": parents, "active_path": active,
            "warnings": warnings, "review_status": "unreviewed", "decisions_confirmed": False}


def memory_record(value: str | Path, source: Path) -> dict[str, object]:
    path = selected_file(value, source)
    if path.suffix.lower() not in (".txt", ".md"):
        fail("UNSUPPORTED_FORMAT")
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        data = stream.read(MAX_MEMORY + 1)
        unchanged(stream, path, before)
    if len(data) > MAX_MEMORY:
        fail("LIMIT_EXCEEDED")
    try:
        text = data.decode("utf-8")
    except UnicodeError:
        fail()
    if not text.strip():
        fail()
    return {"schema_version": 1, "kind": "chatgpt_memory_snapshot", "sha256": sha(data),
            "bytes": len(data), "raw_text": text, "provenance": "user_supplied_memory_text",
            "completeness": "unverified", "review_status": "unreviewed", "decisions_confirmed": False}


def stored(path: Path, expected: bytes) -> bool:
    no_links(path)
    if not path.exists():
        return False
    if not path.is_file() or path.stat().st_size != len(expected):
        fail("CONFLICT")
    with path.open("rb") as stream:
        if stream.read(len(expected) + 1) != expected:
            fail("CONFLICT")
    return True


def publish(path: Path, data: bytes) -> None:
    no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    no_links(path.parent)
    handle, name = tempfile.mkstemp(prefix=".sync-", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        no_links(path)
        if os.name == "nt":
            os.rename(filesystem_path(name), filesystem_path(path))
        else:
            os.link(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def disk_usage(root: Path) -> int:
    size, count = 0, 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            target = Path(directory) / name
            no_links(target)
            count += 1
            if count > MAX_FILES:
                fail("LIMIT_EXCEEDED")
        for name in files:
            target = Path(directory) / name
            if not target.is_file():
                fail()
            size += target.stat().st_size
            if size > INBOX_QUOTA:
                fail("LIMIT_EXCEEDED")
    return size


def sync(config_path: str | Path, history: str | Path | None = None,
         memory: str | Path | None = None) -> SyncResult:
    consent = configuration(config_path)
    result: SyncResult = {"status": "paused", "conversations": 0, "memory_snapshots": 0,
                          "created": 0, "duplicates": 0, "excluded": 0, "warnings": {}}
    if not consent.enabled:
        return result
    if history is None and memory is None:
        fail()
    profile_key = sha(consent.profile.encode("utf-8"))
    objects: dict[str, bytes] = {}
    identities: dict[str, str] = {}
    for _, data in read_history(history, consent.source) if history is not None else []:
        for raw in fragments(data):
            conversation = strict_json(raw)
            if not isinstance(conversation, dict):
                fail()
            conv_id = identity(conversation.get("id", conversation.get("conversation_id")))
            if "conversation_id" in conversation and conversation["conversation_id"] != conv_id:
                fail()
            if conv_id in consent.excluded:
                result["excluded"] += 1
                continue
            digest = sha(raw)
            if conv_id in identities:
                if identities[conv_id] != digest:
                    fail("CONFLICT")
                continue
            identities[conv_id] = digest
            if len(identities) > MAX_CONVERSATIONS:
                fail("LIMIT_EXCEEDED")
            normalized = normalize(conversation)
            for code, count in normalized["warnings"].items():
                result["warnings"][code] = result["warnings"].get(code, 0) + count
            key = sha(("chatgpt\0" + consent.profile + "\0" + conv_id).encode())
            record = {"schema_version": 1, "kind": "chatgpt_conversation_revision",
                      "provider": "chatgpt", "profile_key": profile_key, "session_key": key,
                      "conversation_id": conv_id, "sha256": digest, "bytes": len(raw),
                      "raw_json": raw.decode("utf-8"), "normalized": normalized,
                      "provenance": "chatgpt_export", "normalizer_version": 1}
            objects["conversations/" + key + "/" + digest + ".json"] = encoded(record)
            result["conversations"] += 1
    if memory is not None:
        record = memory_record(memory, consent.source)
        record["profile_key"] = profile_key
        objects["memories/" + cast(str, record["sha256"]) + ".json"] = encoded(record)
        result["memory_snapshots"] = 1
    if not objects:
        result["status"] = "excluded" if result["excluded"] else "empty"
        return result
    if any(len(data) > MAX_REVISION * 3 for data in objects.values()):
        fail("LIMIT_EXCEEDED")
    base = consent.inbox / "chatgpt-sync"
    no_links(base)
    base.mkdir(parents=True, exist_ok=True)
    lock = base / "sync.lock"
    no_links(lock)
    with portalocker.Lock(str(lock), mode="a", timeout=2, check_interval=0.05):
        current = configuration(config_path)
        if not current.enabled:
            result["status"] = "paused"
            return result
        if current != consent:
            fail("CONFLICT")
        root = base / profile_key
        # Receipt is the publication boundary. Consumers only ingest receipt-listed
        # revisions; an interrupted batch is safely completed on repeat invocation.
        receipt = encoded({"schema_version": 1, "kind": "chatgpt_sync_receipt",
                           "profile_key": profile_key, "objects": [
                               {"path": name, "sha256": sha(data)} for name, data in sorted(objects.items())]})
        receipt_path = root / "receipts" / (sha(receipt) + ".json")
        pending: list[tuple[Path, bytes]] = []
        for name, data in objects.items():
            path = root / name
            if stored(path, data):
                result["duplicates"] += 1
            else:
                pending.append((path, data))
        if not stored(receipt_path, receipt):
            pending.append((receipt_path, receipt))
        if disk_usage(base) + sum(len(data) for _, data in pending) > INBOX_QUOTA:
            fail("LIMIT_EXCEEDED")
        for path, data in pending:
            publish(path, data)
        result["created"] = len(objects) - result["duplicates"]
    result["status"] = "synced" if result["created"] else "duplicate"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in local ChatGPT export sync")
    parser.add_argument("--config", required=True)
    parser.add_argument("--history")
    parser.add_argument("--memory")
    args = parser.parse_args()
    try:
        result = sync(args.config, args.history, args.memory)
        sys.stdout.write(json.dumps(result, sort_keys=True) + "\n")
        return 0
    except portalocker.exceptions.LockException:
        code = "BUSY"
    except WorkerError as error:
        code = error.code
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError,
            zipfile.BadZipFile, NotImplementedError, RuntimeError):
        code = "UNAVAILABLE"
    sys.stderr.write("Mind Palace ChatGPT sync: " + code + "\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
