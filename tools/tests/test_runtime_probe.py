"""Synthetic packaging checks. MP_FROZEN_PROBE optionally tests a built bundle."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROBE = Path(__file__).resolve().parents[1] / "probe-runtime.py"


class RuntimeProbeTests(unittest.TestCase):
    def verify(self, command, frozen):
        environment = os.environ.copy()
        if frozen:
            for name in list(environment):
                if name.upper() in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "PATH"):
                    environment.pop(name)
            environment["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
        with tempfile.TemporaryDirectory(prefix="mind-palace-isolated-test-") as directory:
            completed = subprocess.run(command, capture_output=True, timeout=60,
                                       encoding="utf-8", cwd=directory, env=environment)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        for key in ("fts5_query_passed", "atomic_replace_probe_passed",
                    "schema_validation_passed", "cross_process_lock_passed"):
            self.assertIs(result[key], True, key)
        self.assertIs(result["frozen"], frozen)
        self.assertIn("local-model inference", result["pending"])

    def test_source_capabilities(self):
        self.verify([sys.executable, str(PROBE)], False)

    @unittest.skipUnless(os.environ.get("MP_FROZEN_PROBE"), "Frozen bundle not specified")
    def test_frozen_capabilities(self):
        self.verify([os.environ["MP_FROZEN_PROBE"]], True)

    def test_unknown_option_is_rejected(self):
        completed = subprocess.run([sys.executable, str(PROBE), "--arbitrary-command"],
                                   capture_output=True, timeout=15)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, b"")


if __name__ == "__main__":
    unittest.main()
