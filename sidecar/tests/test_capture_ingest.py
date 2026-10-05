import os
import json
from pathlib import Path
import tempfile
import unittest

from memory_worker.capture_control import dispatch as capture_dispatch
from memory_worker.capture_inbox import run_hook
from memory_worker.errors import WorkerError
from memory_worker.service import dispatch
from memory_worker.vault import Vault


def call(vault, method, params):
    return dispatch(vault, {"protocol_version": 1, "id": "test", "method": method, "params": params})


class CaptureIngestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mp-capture-ingest-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.capture_root = self.base / "capture"
        self.source_root = self.base / "source"
        self.source_root.mkdir()
        self.transcript = self.source_root / "session.jsonl"
        self.executable = Path(os.environ.get("MP_CAPTURE_EXECUTABLE", self.base / "receiver.exe"))
        status = capture_dispatch(self.capture_root, {"method": "status"}, self.executable)
        client = next(item for item in status["clients"] if item["provider"] == "codex")
        capture_dispatch(self.capture_root, {"method": "configure", "provider": "codex",
                         "source_root": str(self.source_root), "memory_roots": [], "enabled": True,
                         "memory_enabled": False, "revision": client["revision"]}, self.executable)
        self.config = self.capture_root / "settings/codex.json"
        self.memory = self.capture_root / "settings/codex-memory.json"
        self.vault_root = self.base / "vault"
        self.vault = Vault(self.vault_root, True)

    def capture(self, text):
        self.transcript.write_text(text, encoding="utf-8", newline="")
        result = run_hook(self.config, {"session_id": "synthetic-session", "hook_event_name": "Stop",
                                       "transcript_path": str(self.transcript)}, self.memory)
        self.assertIn(result["status"], ("captured", "duplicate"))

    def plan(self):
        return capture_dispatch(self.capture_root, {"method": "import-plan", "offset": 0}, self.executable)

    def test_one_canonical_session_updates_from_immutable_prefix_revisions(self):
        first = '{"type":"synthetic","text":"one"}\n'
        second = first + '{"type":"synthetic","text":"two"}\n'
        third = second + '{"type":"synthetic","text":"three"}\n'
        self.capture(first)
        self.capture(second)
        plan = self.plan()
        self.assertEqual((len(plan["candidates"]), plan["skipped"], plan["memories_pending"]), (1, 0, 0))
        candidate = plan["candidates"][0]
        self.assertEqual(len(candidate["revisions"]), 2)
        created = call(self.vault, "captures.ingest", candidate)
        self.assertEqual(created["status"], "created")
        acknowledged = capture_dispatch(self.capture_root, {"method": "acknowledge", "provider": "codex",
            "session_key": candidate["session_key"], "selected_sha256": candidate["selected_sha256"],
            "canonical_session_id": created["id"]}, self.executable)
        self.assertEqual(acknowledged["status"], "acknowledged")
        self.assertEqual(capture_dispatch(self.capture_root, {"method": "acknowledge", "provider": "codex",
            "session_key": candidate["session_key"], "selected_sha256": candidate["selected_sha256"],
            "canonical_session_id": created["id"]}, self.executable)["status"], "unchanged")
        self.assertEqual(call(self.vault, "captures.ingest", candidate), created)
        loaded = call(self.vault, "sessions.read", {"id": created["id"]})
        self.assertEqual(loaded["source_text"], second)
        self.assertEqual(loaded["metadata"]["provider"], "codex")
        self.assertEqual(loaded["metadata"]["source_kind"], "hook_capture")

        self.capture(third)
        updated = call(self.vault, "captures.ingest", self.plan()["candidates"][0])
        self.assertEqual(updated, {"id": created["id"], "status": "updated"})
        self.assertEqual(call(Vault(self.vault_root), "sessions.read", {"id": created["id"]})["source_text"], third)
        revision_files = list((self.vault_root / "sources" / loaded["metadata"]["source_id"] / "revisions").glob("*.txt"))
        self.assertEqual(len(revision_files), 2)
        self.assertIn(second.encode(), [item.read_bytes() for item in revision_files])
        self.assertEqual(len(list((self.vault_root / "sessions").glob("*.md"))), 1)

    def test_divergent_capture_is_reported_and_canonical_change_is_preserved(self):
        self.capture('{"type":"synthetic","text":"one"}\n')
        candidate = self.plan()["candidates"][0]
        created = call(self.vault, "captures.ingest", candidate)
        loaded = call(self.vault, "sessions.read", {"id": created["id"]})
        revision = self.vault_root / "sources" / loaded["metadata"]["source_id"] / "revisions" / (candidate["selected_sha256"] + ".txt")
        revision.write_text("changed", encoding="utf-8")
        with self.assertRaises(WorkerError) as changed:
            call(self.vault, "sessions.read", {"id": created["id"]})
        self.assertEqual(changed.exception.code, "CONFLICT")

        self.capture('{"type":"synthetic","text":"other branch"}\n')
        plan = self.plan()
        self.assertEqual(plan["candidates"], [])
        self.assertEqual(plan["skipped"], 1)
        self.assertEqual(revision.read_text(encoding="utf-8"), "changed")

    def test_worker_rejects_spoofed_capture_identity(self):
        self.capture('{"type":"synthetic"}\n')
        candidate = self.plan()["candidates"][0]
        candidate["session_id"] = "different"
        with self.assertRaises(WorkerError) as invalid:
            call(self.vault, "captures.ingest", candidate)
        self.assertEqual(invalid.exception.code, "VALIDATION_ERROR")
        self.assertFalse((self.vault_root / "imports").exists())

    def test_large_latest_revision_imports_complete_text_instead_of_a_stale_prefix(self):
        first = '{"type":"synthetic","text":"one"}\n'
        latest = first + json.dumps({"type": "synthetic", "text": "x" * 280000}) + "\n"
        self.capture(first)
        self.capture(latest)

        plan = self.plan()

        self.assertEqual(len(plan["candidates"]), 1)
        self.assertEqual(plan["skipped"], 0)
        created = call(self.vault, "captures.ingest", plan["candidates"][0])
        self.assertEqual(call(self.vault, "sessions.read", {"id": created["id"]})["source_text"], latest)

    def test_complete_twenty_mib_source_is_stored_and_read_without_truncation(self):
        line = b'{"text":"' + b'x' * (65536 - len(b'{"text":""}\n')) + b'"}\n'
        original = line * 320
        self.assertEqual(len(original), 20 * 1024 * 1024)
        self.capture(original.decode())
        candidate = self.plan()["candidates"][0]
        self.assertEqual(candidate["source_text"].encode(), original)
        receipt = call(self.vault, "captures.ingest", candidate)
        reopened = Vault(self.vault_root)
        self.assertEqual(call(reopened, "sessions.read", {"id": receipt["id"]})["source_text"].encode(), original)


if __name__ == "__main__":
    unittest.main()
