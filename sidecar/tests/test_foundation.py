import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

from memory_worker.atomic_io import digest, file_hash
from memory_worker.errors import WorkerError
from memory_worker.journal import encoded
from memory_worker.paths import owned_path, root_path
from memory_worker.service import dispatch
from memory_worker.vault import Vault

ROOT = Path(__file__).resolve().parents[2]


def op():
    return str(uuid.uuid4())


def call(vault, method, **params):
    return dispatch(vault, {"protocol_version": 1, "id": "test", "method": method, "params": params})


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mp-foundation-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "vault"
        self.vault = Vault(self.root, True)

    def test_source_preservation_and_reopen(self):
        receipt = call(self.vault, "sessions.create", op_id=op(), title="Example", body="Editable summary", source_text="Original\r\nதமிழ்")
        loaded = call(Vault(self.root), "sessions.read", id=receipt["id"])
        self.assertEqual(loaded["source_text"], "Original\r\nதமிழ்")
        original = self.root / "sources" / loaded["metadata"]["source_id"] / "original.txt"
        self.assertEqual(original.read_bytes(), "Original\r\nதமிழ்".encode())
        self.assertEqual(loaded["body"], "Editable summary")
        self.assertEqual(loaded["metadata"]["review_status"], "unreviewed")

    def test_manual_proposal_requires_explicit_confirmation(self):
        receipt = call(self.vault, "decisions.create", op_id=op(), title="Storage", body="Use SQLite")
        record = call(self.vault, "decisions.read", id=receipt["id"])
        self.assertEqual(record["decision_state"], "proposed")
        self.assertEqual(record["evidence_refs"], [])
        with self.assertRaises(WorkerError):
            call(self.vault, "decisions.confirm", op_id=op(), id=receipt["id"], expected_revision=1, confirm=False)
        confirmed = call(self.vault, "decisions.confirm", op_id=op(), id=receipt["id"], expected_revision=1, confirm=True)
        self.assertEqual(confirmed["revision"], 2)
        record = call(Vault(self.root), "decisions.read", id=receipt["id"])
        self.assertEqual(record["confirmation_basis"], "explicit_user_action")
        event = json.loads((self.root / "events" / (receipt["id"] + ".jsonl")).read_text())
        self.assertEqual(event["revision"], 2)
        with self.assertRaises(WorkerError):
            call(self.vault, "decisions.confirm", op_id=op(), id=receipt["id"], expected_revision=1, confirm=True)

    def test_idempotent_operation_and_conflicting_nonce(self):
        nonce = op()
        params = {"op_id": nonce, "title": "Choice", "body": "Example"}
        first = call(self.vault, "decisions.create", **params)
        self.assertEqual(call(Vault(self.root), "decisions.create", **params), first)
        with self.assertRaises(WorkerError):
            call(self.vault, "decisions.create", **{**params, "body": "Different"})
        self.assertEqual(len(list((self.root / "records").glob("*.json"))), 1)

    def test_original_tampering_is_detected_not_overwritten(self):
        receipt = call(self.vault, "sessions.create", op_id=op(), title="Example", body="Summary", source_text="Source")
        loaded = call(self.vault, "sessions.read", id=receipt["id"])
        path = self.root / "sources" / loaded["metadata"]["source_id"] / "original.txt"
        from memory_worker.atomic_io import write
        write(path, b"Externally changed", file_hash(path))
        with self.assertRaises(WorkerError) as error:
            call(self.vault, "sessions.read", id=receipt["id"])
        self.assertEqual(error.exception.code, "CONFLICT")
        self.assertEqual(path.read_bytes(), b"Externally changed")

    def test_real_process_exit_recovery(self):
        nonce = op()
        code = """import os,sys
from memory_worker.vault import Vault
v=Vault(sys.argv[1])
v.call('sessions.create', {'op_id':sys.argv[2], 'title':'Interrupted', 'body':'Summary', 'source_text':'Original'}, lambda _:os._exit(77))
"""
        environment = {**os.environ, "PYTHONPATH": str(ROOT / "sidecar")}
        child = subprocess.run([sys.executable, "-c", code, str(self.root), nonce], env=environment, capture_output=True, timeout=20)
        self.assertEqual(child.returncode, 77, child.stderr.decode())
        intent_path = self.root / ".memory/journal" / (nonce + ".json")
        self.assertFalse(json.loads(intent_path.read_text())["done"])
        reopened = Vault(self.root)
        intent = json.loads(intent_path.read_text())
        self.assertTrue(intent["done"])
        self.assertEqual(call(reopened, "sessions.read", id=intent["result"]["id"])["source_text"], "Original")

    def test_recovery_conflict_retains_external_and_staged_versions(self):
        nonce = op()
        class Interrupted(BaseException):
            pass
        def stop(_):
            raise Interrupted()
        with self.assertRaises(Interrupted):
            self.vault.call("sessions.create", {"op_id": nonce, "title": "Example", "body": "Summary", "source_text": "Original"}, stop)
        intent_path = self.root / ".memory/journal" / (nonce + ".json")
        intent = json.loads(intent_path.read_text())
        target = owned_path(self.root, intent["entries"][0]["path"])
        from memory_worker.atomic_io import write
        write(target, b"External edit", file_hash(target))
        with self.assertRaises(WorkerError) as error:
            Vault(self.root)
        self.assertEqual(error.exception.code, "CONFLICT")
        self.assertEqual(target.read_bytes(), b"External edit")
        self.assertFalse(json.loads(intent_path.read_text())["done"])
        self.assertIn("data", intent["entries"][0])

    def test_invalid_parameters_paths_and_versions(self):
        for method, params in [("sessions.read", {"id": "../../secret"}),
                               ("decisions.create", {"op_id": op(), "title": "Example", "body": "", "decision_state": "confirmed"}),
                               ("sessions.create", {"op_id": op(), "title": "Example", "body": "", "source_text": "x" * 65537})]:
            with self.assertRaises(WorkerError):
                call(self.vault, method, **params)
        with self.assertRaises(WorkerError):
            dispatch(self.vault, {"protocol_version": 2, "id": "x", "method": "health", "params": {}})
        for relative in ["../escape", "records/../escape", "C:/escape", "sources/" + op() + "/other.txt"]:
            with self.assertRaises(WorkerError):
                owned_path(self.root, relative)
        with self.assertRaises(WorkerError):
            root_path(self.root / ".." / "other")

    def test_creation_refuses_existing_vault(self):
        with self.assertRaises(WorkerError):
            Vault(self.root, True)
        self.assertTrue((self.root / ".memory/vault.json").exists())

    def test_invalid_calendar_and_non_utc_timestamps_rejected(self):
        from memory_worker.contracts import validate
        receipt = call(self.vault, "decisions.create", op_id=op(), title="Example", body="Choice")
        record = call(self.vault, "decisions.read", id=receipt["id"])
        for value in ["not-a-date", "2026-02-30T12:00:00Z", "2026-10-02T12:00:00+05:30", "2026-10-02T99:00:00Z"]:
            with self.assertRaises(WorkerError):
                validate("memory-record", {**record, "created_at": value})

    def test_recovery_rejects_tampered_targets(self):
        path = self.root / ".memory/journal" / (op() + ".json")
        from memory_worker.atomic_io import write
        write(path, encoded({"version": 1, "fingerprint": digest(b"x"), "entries": [{"path": "../outside", "old": None, "new": digest(b""), "data": ""}], "result": {}, "done": False}), None)
        with self.assertRaises(WorkerError):
            Vault(self.root)


if __name__ == "__main__":
    unittest.main()
