import importlib.util
import json
from pathlib import Path
import unittest
import os

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("model_probe", ROOT / "tools/probe-models.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ModelProbeTests(unittest.TestCase):
    def test_fixture_coverage(self):
        cases = [json.loads(line) for line in (ROOT / "tools/fixtures/probe-cases.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(cases), 10)
        self.assertEqual(len({case["id"] for case in cases}), 10)
        self.assertEqual({case["expected"] for case in cases}, set(probe.SCHEMA["properties"]["state"]["enum"]))

    def test_invented_evidence_and_wrong_approval_fail(self):
        case = {"id": "proposal", "text": "We should use SQLite", "expected": "proposed"}
        self.assertTrue(probe.validate_output({"state": "proposed", "evidence": "should use SQLite"}, case))
        self.assertFalse(probe.validate_output({"state": "confirmed", "evidence": "should use SQLite"}, case))
        self.assertFalse(probe.validate_output({"state": "proposed", "evidence": "User approved SQLite"}, case))
        self.assertFalse(probe.validate_output({"state": "proposed", "evidence": None}, case))

    def test_absent_subject_requires_abstention(self):
        case = {"id": "missing-recall", "text": "Use SQLite", "expected": "unclear"}
        self.assertTrue(probe.validate_output({"state": "unclear", "evidence": None}, case))
        self.assertFalse(probe.validate_output({"state": "confirmed", "evidence": "Use SQLite"}, case))

    def test_malformed_output_is_rejected(self):
        case = {"id": "proposal", "text": "Use SQLite", "expected": "proposed"}
        self.assertFalse(probe.validate_output([], case))
        self.assertFalse(probe.validate_output({"state": "proposed"}, case))

    @unittest.skipUnless(os.name == "nt", "Windows memory counter")
    def test_process_memory_counter(self):
        self.assertGreater(probe.peak_working_set(os.getpid()), 0)


if __name__ == "__main__":
    unittest.main()
