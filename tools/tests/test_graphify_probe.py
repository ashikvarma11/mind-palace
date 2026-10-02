"""Local AST checks, not a production repository adapter."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile

PROBE = Path(__file__).resolve().parents[1] / "probe-graphify.py"
ROOT = PROBE.parent / "fixtures" / "probe-repo"
spec = importlib.util.spec_from_file_location("graphify_probe", PROBE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GraphifyProbeTests(unittest.TestCase):
    def source_graph(self):
        result = subprocess.run([sys.executable, str(PROBE)], capture_output=True,
                                encoding="utf-8", timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_local_extraction_and_evidence(self):
        graph = self.source_graph()
        module.validate_graph(graph, ROOT)
        self.assertEqual(len(graph["nodes"]), 7)
        self.assertEqual(len(graph["edges"]), 9)
        self.assertEqual(graph["input_tokens"] + graph["output_tokens"], 0)

    def test_changed_evidence_is_rejected(self):
        graph = self.source_graph()
        for field, value in (("source_file", "../outside.ts"), ("source_location", "L999")):
            modified = copy.deepcopy(graph)
            modified["nodes"][0][field] = value
            with self.assertRaises(ValueError):
                module.validate_graph(modified, ROOT)
        graph["edges"][-1]["confidence"] = "EXTRACTED"
        with self.assertRaises(ValueError):
            module.validate_graph(graph, ROOT)

    def test_network_and_process_guard(self):
        for event in ("socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"):
            with self.assertRaises(PermissionError):
                module.deny_network(event, ())
        code = ("import importlib.util,socket; "
                f"s=importlib.util.spec_from_file_location('probe',{str(PROBE)!r}); "
                "m=importlib.util.module_from_spec(s);s.loader.exec_module(m); "
                "m.prepare_environment(); socket.create_connection(('127.0.0.1',9))")
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=15)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"Network and child processes are disabled", result.stderr)

    def test_provider_environment_and_logging_are_disabled(self):
        code = ("import importlib.util,os; "
                f"s=importlib.util.spec_from_file_location('probe',{str(PROBE)!r}); "
                "m=importlib.util.module_from_spec(s);s.loader.exec_module(m); "
                "os.environ['OPENAI_API_KEY']='synthetic-not-a-key'; "
                "os.environ['GRAPHIFY_QUERY_LOG_ENABLE']='1';m.prepare_environment(); "
                "from graphify.querylog import _log_path; "
                "assert 'OPENAI_API_KEY' not in os.environ; assert _log_path() is None")
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(os.environ.get("MP_FROZEN_GRAPHIFY_PROBE"), "Frozen Graphify probe not specified")
    def test_frozen_extraction(self):
        environment = {name: value for name, value in os.environ.items()
                       if name.upper() not in ("PATH", "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV")}
        environment["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
        with tempfile.TemporaryDirectory(prefix="mind-palace-frozen-graph-test-") as directory:
            result = subprocess.run([os.environ["MP_FROZEN_GRAPHIFY_PROBE"]], capture_output=True,
                                    encoding="utf-8", timeout=60, cwd=directory, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        module.validate_graph(json.loads(result.stdout), ROOT)


if __name__ == "__main__":
    unittest.main()
