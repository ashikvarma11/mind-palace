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

import portalocker

from .paths import no_links, root_path
from .errors import WorkerError

MAX_EVENT = 65536
MAX_TRANSCRIPT = 20 * 1024 * 1024
MAX_LINE = 1024 * 1024
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
    return root_path(value)


def configuration(path):
    path = Path(path)
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
    directory = inbox / config["provider"] / key
    no_links(directory)
    directory.mkdir(parents=True, exist_ok=True)
    # Independent processes can fire out of order. Content addressing avoids a mutable
    # latest pointer that a delayed older snapshot could incorrectly roll back.
    lock = inbox / "capture.lock"
    no_links(lock)
    with portalocker.Lock(str(lock), mode="a", timeout=1, check_interval=0.05):
        # Recheck consent inside the lock, before writing anything containing a transcript.
        current, current_source, current_inbox = configuration(config_path)
        if not current["enabled"]:
            return {"status": "paused"}
        if (current, current_source, current_inbox) != (config, source, inbox):
            fail("CONFLICT")
        path = directory / (sha + ".json")
        no_links(path)
        if path.exists():
            with path.open("rb") as stream:
                old = stream.read(MAX_TRANSCRIPT * 6 + MAX_EVENT + 1)
            if len(old) > MAX_TRANSCRIPT * 6 + MAX_EVENT:
                fail("LIMIT_EXCEEDED")
            previous = strict_json(old)
            if not isinstance(previous, dict) or previous.get("session_key") != key or previous.get("provider") != config["provider"] or previous.get("session_id") != session or previous.get("sha256") != sha or previous.get("transcript") != data.decode("utf-8"):
                fail("CONFLICT")
            return {"status": "duplicate", "session_key": key, "sha256": sha, "partial_tail": partial}
        record = {
            "schema_version": 1, "provider": config["provider"], "session_id": session,
            "session_key": key, "sha256": sha, "bytes": len(data),
            "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "normalized": False, "transcript": data.decode("utf-8"),
        }
        raw = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        handle, name = tempfile.mkstemp(prefix=".capture-", dir=directory)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            no_links(path)
            if path.exists():
                fail("CONFLICT")
            # Publish without replacing a concurrent external file, even outside our lock.
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
    try:
        data = sys.stdin.buffer.read(MAX_EVENT + 1)
        if len(data) > MAX_EVENT:
            fail("LIMIT_EXCEEDED")
        result = capture(args.config, strict_json(data))
        # Hook stdout must not inject saved conversation text into the assistant.
        # Non-content stderr gives diagnostics; desktop status integration is still pending.
        sys.stderr.write("Mind Palace capture: " + result["status"] + "\n")
        return 0
    except portalocker.exceptions.LockException:
        sys.stderr.write("Mind Palace capture: BUSY\n")
    except WorkerError as error:
        sys.stderr.write("Mind Palace capture: " + error.code + "\n")
    except (OSError, TypeError, KeyError, ValueError, RecursionError):
        sys.stderr.write("Mind Palace capture: UNAVAILABLE\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
