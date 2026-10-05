"""Privacy-safe adapter for a controlled installed-Codex hook probe."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


MAX_EVENT = 65536
EVENTS = {"SessionStart", "Stop", "SessionEnd"}


def absolute_file(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or not path.is_file():
        raise ValueError("expected an absolute file path")
    return path


def absolute_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise ValueError("expected an absolute path")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a synthetic Codex hook probe")
    parser.add_argument("--receiver", required=True, type=absolute_file)
    parser.add_argument("--config", required=True, type=absolute_file)
    parser.add_argument("--transcript", required=True, type=absolute_file)
    parser.add_argument("--events", required=True, type=absolute_path)
    args = parser.parse_args()

    raw = sys.stdin.buffer.read(MAX_EVENT + 1)
    if len(raw) > MAX_EVENT:
        return 2
    try:
        event = json.loads(raw)
    except (UnicodeError, ValueError, RecursionError):
        return 2
    if not isinstance(event, dict) or event.get("hook_event_name") not in EVENTS:
        return 2

    safe_event = {
        "session_id": "codex_installed_probe",
        "transcript_path": str(args.transcript),
        "cwd": str(args.transcript.parent),
        "hook_event_name": event["hook_event_name"],
        "model": "redacted",
    }
    completed = subprocess.run(
        [str(args.receiver), "--config", str(args.config)],
        input=json.dumps(safe_event).encode("utf-8"),
        capture_output=True,
        timeout=5,
    )
    if completed.returncode != 0 or completed.stdout:
        return 1
    args.events.parent.mkdir(parents=True, exist_ok=True)
    with args.events.open("a", encoding="ascii", newline="\n") as stream:
        stream.write(event["hook_event_name"] + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
