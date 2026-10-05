"""Opt-in local hook receiver. No network, inference, or assistant configuration writes."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import uuid

from .paths import no_links, root_path, filesystem_path
from .errors import WorkerError

MAX_EVENT = 65536
MAX_TRANSCRIPT = 20 * 1024 * 1024
MAX_LINE = 1024 * 1024
INBOX_QUOTA = 1024 * 1024 * 1024
FAILURE_RESERVE = 1024 * 1024
MAX_FAILURE_MARKERS = 1000
EVENTS = {"SessionStart", "UserPromptSubmit", "Stop", "SessionEnd", "Interrupt"}
PROVIDERS = {"claude-code", "codex"}


def fail(code):
    # Never include content, arbitrary paths, or exception strings in hook output.
    raise WorkerError(code, "Local session capture could not complete.")


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail("VALIDATION_ERROR")
            result[key] = value
        return result

    def constant(_):
        fail("VALIDATION_ERROR")

    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError):
        fail("VALIDATION_ERROR")


def dedicated(value):
    if not isinstance(value, str) or not Path(value).is_absolute():
        fail("VALIDATION_ERROR")
    return filesystem_path(root_path(value))


def configuration(path):
    path = filesystem_path(Path(path))
    if not path.is_absolute():
        fail("VALIDATION_ERROR")
    no_links(path)
    with path.open("rb") as stream:
        data = stream.read(MAX_EVENT + 1)
    if len(data) > MAX_EVENT:
        fail("LIMIT_EXCEEDED")
    config = strict_json(data)
    fields = {"schema_version", "provider", "enabled", "source_root", "inbox_root"}
    if not isinstance(config, dict) or set(config) != fields:
        fail("VALIDATION_ERROR")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        fail("VALIDATION_ERROR")
    if not isinstance(config["provider"], str) or config["provider"] not in PROVIDERS or type(config["enabled"]) is not bool:
        fail("VALIDATION_ERROR")
    source, inbox = dedicated(config["source_root"]), dedicated(config["inbox_root"])
    if source == inbox or source in inbox.parents or inbox in source.parents:
        fail("VALIDATION_ERROR")
    if not source.is_dir():
        fail("VALIDATION_ERROR")
    return config, source, inbox


def read_transcript(value, source):
    path = dedicated(value)
    if source not in path.parents or path.suffix != ".jsonl":
        fail("VALIDATION_ERROR")
    no_links(path)
    if not stat.S_ISREG(path.stat().st_mode):
        fail("VALIDATION_ERROR")
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            fail("VALIDATION_ERROR")
        data = stream.read(MAX_TRANSCRIPT + 1)
        after = os.fstat(stream.fileno())
    if len(data) > MAX_TRANSCRIPT:
        fail("LIMIT_EXCEEDED")
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        fail("BUSY")
    # Streaming writers may leave an unfinished final record. Never store it as complete.
    end = data.rfind(b"\n") + 1
    complete = data[:end]
    if not complete:
        return b"", bool(data)
    for line in complete.splitlines():
        if not line or len(line) > MAX_LINE:
            fail("VALIDATION_ERROR")
        if not isinstance(strict_json(line), dict):
            fail("VALIDATION_ERROR")
    try:
        complete.decode("utf-8")
    except UnicodeError:
        fail("VALIDATION_ERROR")
    return complete, end != len(data)


def quota_usage(inbox):
    """Use the last exact app scan plus deliveries created after that scan."""
    health = inbox / "health.json"
    base = 0
    if health.exists():
        no_links(health)
        with health.open("rb") as stream:
            raw = stream.read(MAX_EVENT + 1)
        value = strict_json(raw)
        fields = {"schema_version", "kind", "derived", "bytes_used", "quota_bytes", "failures", "pending_spool", "retention_days", "last_indexed_at"}
        if not isinstance(value, dict) or set(value) != fields or value.get("schema_version") != 1 or value.get("kind") != "capture_health" or value.get("derived") is not True or type(value.get("bytes_used")) is not int or not 0 <= value["bytes_used"] <= INBOX_QUOTA or value.get("quota_bytes") != INBOX_QUOTA:
            fail("REPAIR_REQUIRED")
        base = value["bytes_used"]
    elif inbox.exists():
        total = scanned = 0
        for directory, dirs, files in os.walk(inbox, followlinks=False):
            parent = Path(directory)
            for name in dirs + files:
                no_links(parent / name)
                scanned += 1
                if scanned > 30000:
                    fail("REPAIR_REQUIRED")
            for name in files:
                path = parent / name
                if path == inbox / "capture.lock":
                    continue
                total += path.stat().st_size
                if total > INBOX_QUOTA:
                    fail("QUOTA_EXCEEDED")
        return total
    spool = inbox / "spool"
    pending = 0
    if spool.exists():
        no_links(spool)
        scanned = 0
        for provider in spool.iterdir():
            no_links(provider)
            if not provider.is_dir() or provider.name not in PROVIDERS:
                fail("REPAIR_REQUIRED")
            for item in provider.iterdir():
                no_links(item)
                scanned += 1
                if scanned > 5000 or not item.is_file():
                    fail("REPAIR_REQUIRED")
                pending += item.stat().st_size
    return base + pending


def write_failure_marker(config_path, event, code):
    """Best-effort diagnostic with no session ID, transcript, or source path."""
    if code not in {"BUSY", "CONFLICT", "LIMIT_EXCEEDED", "QUOTA_EXCEEDED", "REPAIR_REQUIRED", "UNAVAILABLE", "VALIDATION_ERROR"}:
        code = "UNAVAILABLE"
    try:
        config, _, inbox = configuration(config_path)
        if not config["enabled"]:
            return
        event_name = event.get("hook_event_name") if isinstance(event, dict) else None
        if event_name not in EVENTS:
            event_name = "unknown"
        directory = inbox / "failures"
        no_links(directory)
        directory.mkdir(parents=True, exist_ok=True)
        if sum(1 for item in directory.iterdir() if item.is_file()) >= MAX_FAILURE_MARKERS:
            return
        marker = {"schema_version": 1, "kind": "capture_failure", "provider": config["provider"],
                  "event": event_name, "code": code,
                  "occurred_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        raw = json.dumps(marker, separators=(",", ":"), sort_keys=True).encode()
        path = directory / (uuid.uuid4().hex + ".json")
        handle, name = tempfile.mkstemp(prefix=".failure-", dir=directory)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.rename(name, path) if os.name == "nt" else os.link(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    except (OSError, WorkerError, TypeError, ValueError):
        return


def capture(config_path, event):
    config, source, inbox = configuration(config_path)
    if not config["enabled"]:
        return {"status": "paused"}
    if not isinstance(event, dict) or not isinstance(event.get("hook_event_name"), str) or event["hook_event_name"] not in EVENTS:
        fail("VALIDATION_ERROR")
    session = event.get("session_id")
    if not isinstance(session, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session):
        fail("VALIDATION_ERROR")
    if event.get("transcript_path") is None:
        return {"status": "unavailable"}
    data, partial = read_transcript(event["transcript_path"], source)
    if not data:
        return {"status": "waiting", "partial_tail": partial}
    sha = hashlib.sha256(data).hexdigest()
    key = hashlib.sha256((config["provider"] + "\0" + session).encode()).hexdigest()
    # The synchronous hook publishes one unique delivery and never waits for the
    # shared app-operation lock. Validation, deduplication, and canonical
    # content-addressed publication happen later during app-side indexing.
    directory = inbox / "spool" / config["provider"]
    no_links(directory)
    directory.mkdir(parents=True, exist_ok=True)
    current, current_source, current_inbox = configuration(config_path)
    if not current["enabled"]:
        return {"status": "paused"}
    if (current, current_source, current_inbox) != (config, source, inbox):
        fail("CONFLICT")
    record = {
        "schema_version": 1, "provider": config["provider"], "session_id": session,
        "session_key": key, "sha256": sha, "bytes": len(data),
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "normalized": False, "transcript": data.decode("utf-8"),
    }
    raw = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if quota_usage(inbox) + len(raw) > INBOX_QUOTA - FAILURE_RESERVE:
        fail("QUOTA_EXCEEDED")
    path = directory / (uuid.uuid4().hex + ".json")
    no_links(path)
    handle, name = tempfile.mkstemp(prefix=".capture-", dir=directory)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        no_links(path)
        if path.exists():
            fail("CONFLICT")
        if os.name == "nt":
            os.rename(name, path)
        else:
            os.link(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return {"status": "captured", "session_key": key, "sha256": sha, "partial_tail": partial}


def main():
    parser = argparse.ArgumentParser(description="Local opt-in session hook receiver")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    event = None
    try:
        data = sys.stdin.buffer.read(MAX_EVENT + 1)
        if len(data) > MAX_EVENT:
            fail("LIMIT_EXCEEDED")
        event = strict_json(data)
        result = capture(args.config, event)
        # Hook stdout must not inject saved conversation text into the assistant.
        # Non-content stderr gives diagnostics; desktop status integration is still pending.
        sys.stderr.write("Mind Palace capture: " + result["status"] + "\n")
        return 0
    except WorkerError as error:
        write_failure_marker(args.config, event, error.code)
        sys.stderr.write("Mind Palace capture: " + error.code + "\n")
    except (OSError, TypeError, KeyError, ValueError, RecursionError):
        write_failure_marker(args.config, event, "UNAVAILABLE")
        sys.stderr.write("Mind Palace capture: UNAVAILABLE\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
