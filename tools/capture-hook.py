"""Source/frozen capture entry point. Does not install or register any assistant hook."""
from pathlib import Path
import sys

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sidecar"))

from memory_worker.capture_inbox import main

if __name__ == "__main__":
    raise SystemExit(main())
