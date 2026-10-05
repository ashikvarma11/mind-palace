"""Measure the frozen capture receiver with temporary synthetic data only."""

import argparse
import json
import math
from pathlib import Path
import statistics
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXECUTABLE = ROOT / ".tools" / "capture-dist" / "memory-capture" / "memory-capture.exe"
FIXTURE = ROOT / "sidecar" / "tests" / "fixtures" / "codex-hook-events.json"


def bounded_integer(minimum: int, maximum: int):
    def parse(value: str) -> int:
        number = int(value)
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(f"must be from {minimum} through {maximum}")
        return number
    return parse


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure synthetic frozen hook latency")
    parser.add_argument("--executable", type=Path, default=DEFAULT_EXECUTABLE)
    parser.add_argument("--runs", type=bounded_integer(1, 30), default=10)
    parser.add_argument("--deadline-ms", type=bounded_integer(100, 60000), default=3000)
    parser.add_argument("--source-mib", type=bounded_integer(0, 20), default=0)
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        parser.error("capture executable was not found")

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    lines = fixture["transcript_lines"]
    template = next(event for event in fixture["events"]
                    if event["hook_event_name"] == "SessionEnd")
    raw = ("\n".join(lines) + "\n").encode("utf-8")
    if args.source_mib:
        prefix, suffix = b'{"type":"synthetic","text":"', b'"}\n'
        line = prefix + b"x" * (65536 - len(prefix) - len(suffix)) + suffix
        raw = line * (args.source_mib * 16)
    process_timeout = max(5.0, min(60.0, args.deadline_ms * 2 / 1000))
    durations: list[float] = []
    return_codes: list[int | None] = []
    empty_stdout: list[bool] = []

    with tempfile.TemporaryDirectory(prefix="mp-hook-deadline-") as directory:
        root = Path(directory)
        source = root / "source"
        source.mkdir()
        transcript = source / "session.jsonl"
        transcript.write_bytes(raw)
        config = root / "consent.json"
        config.write_text(json.dumps({
            "schema_version": 1,
            "provider": "codex",
            "enabled": True,
            "source_root": str(source),
            "inbox_root": str(root / "inbox"),
        }), encoding="utf-8")

        for index in range(args.runs):
            event = dict(template)
            event["session_id"] = f"deadline_fixture_{index:02d}"
            event["transcript_path"] = str(transcript)
            started = time.perf_counter()
            try:
                completed = subprocess.run(
                    [str(executable), "--config", str(config)],
                    input=json.dumps(event).encode("utf-8"),
                    capture_output=True,
                    timeout=process_timeout,
                )
                return_codes.append(completed.returncode)
                empty_stdout.append(completed.stdout == b"")
            except subprocess.TimeoutExpired:
                return_codes.append(None)
                empty_stdout.append(False)
            durations.append((time.perf_counter() - started) * 1000)

    successful = sum(code == 0 for code in return_codes)
    within = sum(code == 0 and empty and duration <= args.deadline_ms
                 for code, empty, duration in zip(return_codes, empty_stdout, durations))
    report = {
        "schema_version": 1,
        "fixture": "codex SessionEnd synthetic",
        "executable": executable.name,
        "runs": args.runs,
        "source_bytes": len(raw),
        "deadline_ms": args.deadline_ms,
        "process_timeout_ms": round(process_timeout * 1000),
        "successful": successful,
        "empty_stdout": sum(empty_stdout),
        "within_deadline": within,
        "median_ms": round(statistics.median(durations), 3),
        "p95_ms": round(percentile(durations, 0.95), 3),
        "maximum_ms": round(max(durations), 3),
        "durations_ms": [round(value, 3) for value in durations],
        "result": "pass" if within == args.runs else "fail",
    }
    print(json.dumps(report, separators=(",", ":")))
    return 0 if report["result"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
