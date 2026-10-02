"""Step 02 capability probe: actual runtime checks, no model/packaging claims."""
import importlib.util
import json
import os
import platform
import sqlite3
import tempfile
from pathlib import Path


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
    return {"platform": platform.system(), "architecture": platform.machine(),
            "python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
            "fts5_query_passed": matches == 1, "atomic_replace_probe_passed": atomic_replace,
            "packages_available": packages,
            "pending": ["cross-process locking", "worker freezing", "Graphify extraction",
                        "local-model inference", "native desktop", "clean-machine installer"]}


if __name__ == "__main__":
    result = probe()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["fts5_query_passed"] and result["atomic_replace_probe_passed"] else 1)
