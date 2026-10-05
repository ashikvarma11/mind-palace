"""Stage only the dedicated bounded capture bundle; do not register assistant hooks."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("worker_staging", Path(__file__).with_name("stage-worker.py"))
assert spec and spec.loader
staging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(staging)
staging.EXE = "memory-capture.exe"
staging.SOURCE = ".tools/capture-dist/memory-capture"
staging.TARGET = "src-tauri/resources/memory-capture"

if __name__ == "__main__":
    staging.main()
