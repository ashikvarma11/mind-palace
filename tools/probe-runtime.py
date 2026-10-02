"""Step 02 capability probe: actual runtime checks, no model/packaging claims."""
import importlib.util
import json
import os
import platform
import sqlite3
import tempfile
import subprocess
import sys
import argparse
from pathlib import Path


def child_command(path):
    executable = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, str(Path(__file__).resolve())]
    return executable + ["--lock-child", str(path)]


def attempt_lock(path):
    import portalocker
    try:
        with portalocker.Lock(path, mode="a", timeout=0):
            return 0
    except portalocker.exceptions.LockException:
        return 3


def dependency_probes():
    from jsonschema import Draft202012Validator
    import portalocker
    schema = {"type": "object", "properties": {"schema_version": {"const": 1}},
              "required": ["schema_version"], "additionalProperties": False}
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    schema_passed = validator.is_valid({"schema_version": 1}) and all(
        not validator.is_valid(value) for value in
        ({"schema_version": 2}, {}, {"schema_version": 1, "unexpected": True}))
    with tempfile.TemporaryDirectory(prefix="mind-palace-lock-probe-") as directory:
        lock_path = Path(directory) / "synthetic.lock"
        with portalocker.Lock(lock_path, mode="a", timeout=0):
            blocked = subprocess.run(child_command(lock_path), capture_output=True, timeout=15).returncode == 3
        released = subprocess.run(child_command(lock_path), capture_output=True, timeout=15).returncode == 0
    return {"schema_validation_passed": schema_passed,
            "cross_process_lock_passed": blocked and released}


def probe():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE VIRTUAL TABLE probe USING fts5(body)")
    db.execute("INSERT INTO probe(body) VALUES (?)", ("Preserve source evidence",))
    matches = db.execute("SELECT count(*) FROM probe WHERE probe MATCH ?", ("evidence",)).fetchone()[0]
    db.close()
    with tempfile.TemporaryDirectory(prefix="mind-palace-probe-") as directory:
        root = Path(directory)
        staging, target = root / "staging.txt", root / "record.txt"
        with staging.open("w", encoding="utf-8") as handle:
            handle.write("Synthetic probe only: café 🏰")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staging, target)
        atomic_replace = target.read_text(encoding="utf-8") == "Synthetic probe only: café 🏰"
    packages = {name: importlib.util.find_spec(name) is not None for name in
                ("jsonschema", "portalocker", "pytest", "PyInstaller", "mcp", "graphify")}
    result = {"platform": platform.system(), "architecture": platform.machine(),
            "python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
            "fts5_query_passed": matches == 1, "atomic_replace_probe_passed": atomic_replace,
            "packages_available": packages,
            "frozen": bool(getattr(sys, "frozen", False)),
            "pending": ["production worker transport", "Graphify extraction",
                        "local-model inference", "native desktop", "clean-machine installer"]}
    if packages["jsonschema"] and packages["portalocker"]:
        result.update(dependency_probes())
    else:
        result["pending"].append("schema validation and cross-process locking")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock-child", type=Path, help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    if arguments.lock_child is not None:
        raise SystemExit(attempt_lock(arguments.lock_child))
    result = probe()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    checks = [value for key, value in result.items() if key.endswith("_passed")]
    raise SystemExit(0 if all(checks) else 1)
