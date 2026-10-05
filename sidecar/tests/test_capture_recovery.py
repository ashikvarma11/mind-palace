"""Synthetic recovery/history/retention checks with exact original evidence."""
import datetime
import json
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest.mock import patch

from memory_worker.capture_control import dispatch
from memory_worker.capture_inbox import read_session_snapshot, run_hook
from memory_worker.errors import WorkerError
from memory_worker.service import dispatch as vault_dispatch
from memory_worker.vault import Vault


class CaptureRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mp-recovery-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "capture"
        self.source = self.base / "source"
        self.source.mkdir()
        self.exe = self.base / "receiver.exe"
        self.config = self.root / "settings/codex.json"
        initial = dispatch(self.root, {"method": "status"}, self.exe)
        revision = next(item for item in initial["clients"] if item["provider"] == "codex")["revision"]
        dispatch(self.root, {"method": "configure", "provider": "codex", "source_root": str(self.source),
                            "memory_roots": [], "enabled": True, "memory_enabled": False, "revision": revision}, self.exe)
        self.session = str(uuid.uuid4())
        self.path = self.source / "rollout.jsonl"
        self.path.write_text(json.dumps({"type": "session_meta", "payload": {"id": self.session,
                             "timestamp": "2026-10-04T00:00:00Z"}}) + "\n", encoding="utf-8")

    def call(self, method, **fields):
        return dispatch(self.root, {"method": method, **fields}, self.exe)

    def append(self, text, role="user"):
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"type": "response_item", "payload": {"type": "message", "role": role,
                         "content": [{"type": "input_text" if role == "user" else "output_text", "text": text}]}}) + "\n")

    def capture(self):
        return run_hook(self.config, {"hook_event_name": "Stop", "session_id": self.session,
                                     "transcript_path": str(self.path)})

    def test_repair_known_session_recovers_exit_tail_without_collecting_unknown_history(self):
        self.append("Initial synthetic conversation")
        self.capture()
        self.call("index")
        self.append("Final synthetic record after a forced exit")
        unknown = self.source / "unknown.jsonl"
        unknown.write_text(json.dumps({"type": "session_meta", "payload": {"id": "unapproved-history"}}) + "\n")
        recovered = self.call("recover")
        self.assertEqual(recovered["restored"], 1)
        plan = self.call("import-plan", offset=0)
        self.assertEqual(len(plan["candidates"]), 1)
        self.assertEqual(plan["candidates"][0]["source_text"].encode(), self.path.read_bytes())
        self.assertEqual(self.call("recover")["restored"], 0)

    def test_history_requires_exact_preview_confirmation_and_preserves_sources(self):
        self.append("Synthetic old history")
        original = self.path.read_bytes()
        self.call("index")
        self.assertEqual(self.call("import-plan", offset=0)["candidates"], [])
        preview = self.call("history-preview")
        self.assertEqual((preview["sessions"], preview["files"], preview["bytes"]), (1, 1, len(original)))
        self.assertEqual(preview["earliest"], "2026-10-04T00:00:00Z")
        self.assertEqual(self.call("import-plan", offset=0)["candidates"], [])
        result = self.call("history-import", preview_id=preview["preview_id"], offset=0)
        self.assertEqual((result["captured"], result["next_offset"]), (1, None))
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(self.call("import-plan", offset=0)["candidates"][0]["source_text"].encode(), original)

    def test_history_changed_source_is_skipped_and_scope_revision_invalidates_confirmation(self):
        preview = self.call("history-preview")
        self.append("Changed after preview")
        self.assertEqual(self.call("history-import", preview_id=preview["preview_id"], offset=0)["skipped"], 1)
        preview = self.call("history-preview")
        config = json.loads(self.config.read_bytes())
        config["enabled"] = False
        self.config.write_text(json.dumps(config))
        with self.assertRaises(WorkerError):
            self.call("history-import", preview_id=preview["preview_id"], offset=0)

    def test_history_source_change_during_read_does_not_publish_capture(self):
        from memory_worker.session_capture import read_transcript
        preview = self.call("history-preview")
        def changed(path, source):
            result = read_transcript(path, source)
            self.append("Changed while the confirmed file was read")
            return result
        with patch("memory_worker.capture_recovery.read_transcript", side_effect=changed):
            result = self.call("history-import", preview_id=preview["preview_id"], offset=0)
        self.assertEqual((result["captured"], result["skipped"]), (0, 1))
        self.assertEqual(self.call("import-plan", offset=0)["candidates"], [])

    def test_paused_recovery_keeps_existing_scope_and_history_preview_rejects_path_injection(self):
        self.capture()
        self.call("index")
        config = json.loads(self.config.read_bytes())
        config["enabled"] = False
        self.config.write_text(json.dumps(config))
        self.append("Must not auto capture while paused")
        self.assertEqual(self.call("recover")["restored"], 0)
        with self.assertRaises(WorkerError):
            self.call("history-import", preview_id="../escape", offset=0)

    def test_cleanup_removes_only_old_imported_prefixes_and_keeps_shared_source_bytes(self):
        self.append("Old prefix " + "a" * 40000)
        self.capture()
        self.call("index")
        first = self.call("import-plan", offset=0)["candidates"][0]
        folder = self.root / "inbox/codex" / first["session_key"]
        old = folder / (first["selected_sha256"] + ".json")
        record = json.loads(old.read_bytes())
        record["captured_at"] = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=31)).isoformat()
        old.write_text(json.dumps(record))
        self.assertEqual(self.call("cleanup")["removed_revisions"], 0)
        self.append("SQLite is the approved test database", "assistant")
        self.capture()
        plan = self.call("import-plan", offset=0)
        candidate = plan["candidates"][0]
        vault = Vault(self.base / "vault", create=True)
        receipt = vault_dispatch(vault, {"protocol_version": 1, "id": "retention", "method": "captures.ingest", "params": candidate})
        self.call("acknowledge", provider="codex", session_key=candidate["session_key"],
                  selected_sha256=candidate["selected_sha256"], canonical_session_id=receipt["id"])
        result = self.call("cleanup")
        self.assertEqual(result["removed_revisions"], 1)
        self.assertFalse(old.exists())
        selected = folder / (candidate["selected_sha256"] + ".json")
        self.assertEqual(read_session_snapshot(selected, "codex", candidate["session_key"])[1], self.path.read_bytes())
        self.assertEqual(self.call("cleanup")["removed_revisions"], 0)

    def test_cleanup_preserves_divergent_or_recent_revisions_and_rejects_tampered_ack(self):
        self.append("Old common prefix")
        self.capture()
        first = self.call("import-plan", offset=0)["candidates"][0]
        self.append("Selected complete conversation")
        self.capture()
        selected = self.call("import-plan", offset=0)["candidates"][0]
        self.call("acknowledge", provider="codex", session_key=selected["session_key"],
                  selected_sha256=selected["selected_sha256"], canonical_session_id=str(uuid.uuid4()))
        self.assertEqual(self.call("cleanup")["removed_revisions"], 0)
        folder = self.root / "inbox/codex" / selected["session_key"]
        header = self.path.read_text().splitlines()[0] + "\n"
        self.path.write_text(header)
        self.append("Unimported divergent branch")
        self.capture()
        self.call("import-plan", offset=0)
        branch = next(path for path in folder.iterdir() if path.stem not in {first["selected_sha256"], selected["selected_sha256"]})
        metadata = json.loads(branch.read_bytes())
        metadata["captured_at"] = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=31)).isoformat()
        branch.write_text(json.dumps(metadata))
        self.assertEqual(self.call("cleanup")["removed_revisions"], 0)
        self.assertTrue(branch.exists())
        ack = self.root / "inbox/imported/codex" / (selected["session_key"] + ".json")
        ack.write_text('{"selected_sha256":"invalid"}')
        before = set(folder.iterdir())
        with self.assertRaises(WorkerError):
            self.call("cleanup")
        self.assertEqual(set(folder.iterdir()), before)

    def test_cleanup_budget_defers_without_deleting_any_file(self):
        self.capture()
        self.call("index")
        before = {path: path.read_bytes() for path in (self.root / "inbox/codex").rglob("*.json")}
        with patch("memory_worker.capture_inbox.MAX_INDEX_SCAN", 1):
            result = self.call("cleanup")
        self.assertTrue(result["deferred"])
        self.assertEqual(result["removed_revisions"], 0)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_codex_ask_excludes_setup_instructions_and_verifies_escaped_exact_quote(self):
        self.append("Database local vault Neptune from a setup instruction", "developer")
        self.append('We selected SQLite for the local vault database. "Quoted" café 🧠')
        self.capture()
        candidate = self.call("import-plan", offset=0)["candidates"][0]
        vault = Vault(self.base / "vault", create=True)
        vault_dispatch(vault, {"protocol_version": 1, "id": "ask", "method": "captures.ingest", "params": candidate})
        answer = vault.ask_sessions("Which database did we select for the local vault?")
        self.assertEqual(answer["status"], "answered")
        self.assertIn("SQLite", answer["answer"])
        self.assertNotIn("Neptune", answer["answer"])
        for source in answer["sources"]:
            self.assertEqual(candidate["source_text"][source["start"]:source["end"]], source["quote"])
        self.assertEqual(vault.ask_sessions("Was Neptune selected?")["status"], "insufficient_evidence")


if __name__ == "__main__":
    unittest.main()
