import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_foundation import op
from memory_worker.protocol import MAX_FRAME, serve
from memory_worker.vault import Vault

ROOT = Path(__file__).resolve().parents[2]


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mp-protocol-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "vault"

    def request(self, frame):
        outgoing = io.BytesIO()
        code = serve(Vault(self.root, not self.root.exists()), io.BytesIO(frame), outgoing)
        return code, json.loads(outgoing.getvalue())

    def test_health_no_ai(self):
        _, response = self.request(b'{"protocol_version":1,"id":"h","method":"health","params":{}}\n')
        self.assertFalse(response["result"]["ai_enabled"])

    def test_bad_json_utf8_duplicates_and_nonfinite(self):
        for frame in [b'{}\xff\n', b'{"id":"a","id":"b"}\n', b'{"x":NaN}\n', b'{\n', b'{"id":"\\ud800"}\n']:
            _, response = self.request(frame)
            self.assertEqual(response["error"]["code"], "PROTOCOL_ERROR")
            self.assertNotIn(str(self.root), json.dumps(response))

    def test_oversize_and_truncated_fail_closed(self):
        for frame in [b"x" * (MAX_FRAME + 1), b'{}']:
            code, response = self.request(frame)
            self.assertEqual(code, 1)
            self.assertEqual(response["error"]["code"], "PROTOCOL_ERROR")

    def test_unknown_method_and_missing_record(self):
        _, response = self.request(b'{"protocol_version":1,"id":"h","method":"shell","params":{}}\n')
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        request = {"protocol_version": 1, "id": "missing", "method": "decisions.read", "params": {"id": op()}}
        _, response = self.request((json.dumps(request) + "\n").encode())
        self.assertEqual(response["error"]["code"], "NOT_FOUND")

    def process_flow(self, command):
        env = {key: value for key, value in os.environ.items() if key.upper() in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH")}
        if len(command) == 1:
            env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
        else:
            env["PYTHONPATH"] = str(ROOT / "sidecar")
        request = {"protocol_version": 1, "id": "create", "method": "sessions.create", "params": {"op_id": op(), "title": "Synthetic", "body": "Summary", "source_text": "Original"}}
        child = subprocess.run(command + ["--mode", "ui", "--vault", str(self.root), "--create-vault"],
                               input=(json.dumps(request) + "\n").encode(), capture_output=True, timeout=30, env=env)
        self.assertEqual(child.returncode, 0, child.stderr.decode())
        receipt = json.loads(child.stdout)
        request.update(id="read", method="sessions.read", params={"id": receipt["result"]["id"]})
        child = subprocess.run(command + ["--mode", "ui", "--vault", str(self.root)],
                               input=(json.dumps(request) + "\n").encode(), capture_output=True, timeout=30, env=env)
        self.assertEqual(child.returncode, 0, child.stderr.decode())
        self.assertEqual(json.loads(child.stdout)["result"]["source_text"], "Original")
        self.assertEqual(child.stderr, b"")
        preview = {"protocol_version": 1, "id": "preview", "method": "cloud.preview", "params": {
            "provider": "anthropic", "model": "synthetic-test-model", "question": "What was recorded?", "max_output_tokens": 128,
            "selections": [{"kind": "session", "id": receipt["result"]["id"], "start": 0, "end": 8}]}}
        child = subprocess.run(command + ["--mode", "ui", "--vault", str(self.root)],
                               input=(json.dumps(preview) + "\n").encode(), capture_output=True, timeout=30, env=env)
        self.assertEqual(child.returncode, 0, child.stderr.decode())
        result = json.loads(child.stdout)["result"]
        self.assertFalse(result["can_send"])
        self.assertEqual(json.loads(result["request"]["body"]["messages"][0]["content"])["sources"][0]["text"], "Original")
        self.assertEqual(child.stderr, b"")
        from memory_worker.atomic_io import write, file_hash
        from memory_worker.journal import encoded
        decision = {"protocol_version": 1, "id": "decision", "method": "decisions.create", "params": {"op_id": op(), "title": "Synthetic choice", "body": "Example"}}
        child = subprocess.run(command + ["--mode", "ui", "--vault", str(self.root)],
                               input=(json.dumps(decision) + "\n").encode(), capture_output=True, timeout=30, env=env)
        self.assertEqual(child.returncode, 0, child.stderr.decode())
        record_id = json.loads(child.stdout)["result"]["id"]
        path = self.root / "records" / (record_id + ".json")
        value = json.loads(path.read_text())
        value["created_at"] = "not-a-date"
        write(path, encoded(value), file_hash(path))
        decision.update(id="invalid-date", method="decisions.read", params={"id": record_id})
        child = subprocess.run(command + ["--mode", "ui", "--vault", str(self.root)],
                               input=(json.dumps(decision) + "\n").encode(), capture_output=True, timeout=30, env=env)
        self.assertEqual(json.loads(child.stdout)["error"]["code"], "VALIDATION_ERROR")

    def test_source_process_reopen(self):
        self.process_flow([sys.executable, "-m", "memory_worker"])

    @unittest.skipUnless(os.environ.get("MP_FROZEN_WORKER"), "Frozen worker not selected")
    def test_frozen_process_reopen(self):
        self.process_flow([os.environ["MP_FROZEN_WORKER"]])


if __name__ == "__main__":
    unittest.main()
