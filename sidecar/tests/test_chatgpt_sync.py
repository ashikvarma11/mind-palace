"""Synthetic exports only. These tests never open an assistant account or user store."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from memory_worker import chatgpt_sync as module
from memory_worker.errors import WorkerError


def conversation(session="session-one"):
    def node(key, parent, role, text):
        return {"id": key, "parent": parent, "children": [], "message": {
            "id": "message-" + key, "author": {"role": role},
            "content": {"content_type": "text", "parts": [text]}, "create_time": 1700000000,
            "metadata": {}, "recipient": "all"}}
    return {"id": session, "title": "Fictional project", "create_time": 1700000000,
            "current_node": "answer-b", "mapping": {
                "root": {"id": "root", "parent": None, "message": None},
                "user": node("user", "root", "user", "தமிழ் 🧠\r\n<script>inert</script>"),
                "answer-a": node("answer-a", "user", "assistant", "A suggestion, never approval."),
                "answer-b": node("answer-b", "user", "assistant", "Alternative suggestion.")}}


class ChatGPTSyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mp-chatgpt-sync-")
        self.addCleanup(self.cleanup)
        self.root = module.filesystem_path(Path(self.temporary.name))
        self.source = self.root / "source"
        self.source.mkdir()
        self.inbox = self.root / "inbox"
        self.config_path = self.root / "consent.json"
        self.config = {"schema_version": 1, "enabled": True, "profile": "synthetic-personal",
                       "source_root": str(self.source), "inbox_root": str(self.inbox),
                       "excluded_conversation_ids": []}
        self.configure()
        self.history = self.source / "conversations.json"
        self.raw = json.dumps(conversation(), ensure_ascii=False, indent=2).encode()
        self.history.write_bytes(b"[\r\n" + self.raw + b"\r\n]")

    def cleanup(self):
        # Restrict deletion to the exact directory allocated by this test harness.
        allocated = Path(self.temporary.name).resolve()
        if allocated.parent != Path(tempfile.gettempdir()).resolve() or not allocated.name.startswith("mp-chatgpt-sync-"):
            raise AssertionError("Unexpected test cleanup root")
        target = module.filesystem_path(allocated)
        if target.exists():
            shutil.rmtree(target)
        self.temporary.cleanup()

    def configure(self, **changes):
        self.config.update(changes)
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")

    def records(self, kind="conversations"):
        return sorted((self.inbox / "chatgpt-sync").glob("*/" + kind + "/**/*.json"))

    def run_sync(self, **kwargs):
        return module.sync(self.config_path, **kwargs)

    def test_original_bytes_branches_and_unreviewed_provenance(self):
        result = self.run_sync(history=self.history)
        self.assertEqual((result["status"], result["created"]), ("synced", 1))
        record = json.loads(self.records()[0].read_bytes())
        self.assertEqual(record["raw_json"].encode(), self.raw)
        self.assertEqual(record["sha256"], module.sha(self.raw))
        normalized = record["normalized"]
        self.assertEqual(normalized["active_path"], ["root", "user", "answer-b"])
        self.assertEqual({item["node_id"] for item in normalized["messages"]}, {"user", "answer-a", "answer-b"})
        self.assertEqual(normalized["review_status"], "unreviewed")
        self.assertFalse(normalized["decisions_confirmed"])
        user = next(item for item in normalized["messages"] if item["role"] == "user")
        self.assertEqual(user["source_pointer"], "/mapping/user/message")
        self.assertIn("<script>", user["text_parts"][0])

    def test_repeat_and_new_revision_keep_one_session_identity(self):
        self.run_sync(history=self.history)
        first = self.records()[0]
        original, modified = first.read_bytes(), first.stat().st_mtime_ns
        repeated = self.run_sync(history=self.history)
        self.assertEqual((repeated["created"], repeated["duplicates"]), (0, 1))
        self.assertEqual(first.stat().st_mtime_ns, modified)
        changed = conversation()
        changed["mapping"]["answer-b"]["message"]["content"]["parts"] = ["Resumed work"]
        self.history.write_text(json.dumps([changed]), encoding="utf-8")
        self.assertEqual(self.run_sync(history=self.history)["created"], 1)
        records = self.records()
        self.assertEqual(len(records), 2)
        self.assertEqual(len({path.parent for path in records}), 1)
        self.assertEqual(first.read_bytes(), original)

    def test_profile_separates_same_provider_id(self):
        self.run_sync(history=self.history)
        self.configure(profile="synthetic-work")
        self.run_sync(history=self.history)
        records = [json.loads(path.read_bytes()) for path in self.records()]
        self.assertEqual(len({record["session_key"] for record in records}), 2)

    def test_memory_only_is_separate_exact_and_not_complete_or_approved(self):
        memory = self.source / "saved-memory.txt"
        data = "Fictional preference\r\nதமிழ்".encode()
        memory.write_bytes(data)
        result = self.run_sync(memory=memory)
        self.assertEqual(result["memory_snapshots"], 1)
        record = json.loads(self.records("memories")[0].read_bytes())
        self.assertEqual(record["raw_text"].encode(), data)
        self.assertEqual(record["completeness"], "unverified")
        self.assertEqual(record["provenance"], "user_supplied_memory_text")
        self.assertFalse(record["decisions_confirmed"])
        self.assertEqual(self.records(), [])
        self.assertEqual(self.run_sync(memory=memory)["status"], "duplicate")

    def test_zip_partitions_only_import_history_not_account_metadata_or_assets(self):
        archive = self.source / "export.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
            zipped.writestr("conversations-000.json", self.history.read_bytes())
            zipped.writestr("conversations-001.json", json.dumps([conversation("session-two")]))
            zipped.writestr("user.json", "FICTIONAL_ACCOUNT_SECRET")
            zipped.writestr("../evil.txt", "Never extracted")
        result = self.run_sync(history=archive)
        self.assertEqual(result["conversations"], 2)
        self.assertFalse((self.root / "evil.txt").exists())
        for path in self.records():
            self.assertNotIn(b"FICTIONAL_ACCOUNT_SECRET", path.read_bytes())

    def test_exclusions_never_persist_excluded_originals(self):
        excluded = conversation("excluded-session")
        excluded["title"] = "EXCLUDED_PRIVATE_MARKER"
        self.history.write_text(json.dumps([conversation(), excluded]), encoding="utf-8")
        self.configure(excluded_conversation_ids=["excluded-session"])
        result = self.run_sync(history=self.history)
        self.assertEqual((result["conversations"], result["excluded"]), (1, 1))
        for path in self.inbox.rglob("*.json"):
            self.assertNotIn(b"EXCLUDED_PRIVATE_MARKER", path.read_bytes())

    def test_paused_never_reads_or_creates_content(self):
        self.configure(enabled=False)
        with patch.object(module, "read_history", side_effect=AssertionError("must not read")):
            self.assertEqual(self.run_sync(history=self.history)["status"], "paused")
        self.assertFalse(self.inbox.exists())

    def test_pause_during_read_is_rechecked_before_publication(self):
        original = module.read_history
        def pause(*args):
            value = original(*args)
            self.configure(enabled=False)
            return value
        with patch.object(module, "read_history", side_effect=pause):
            self.assertEqual(self.run_sync(history=self.history)["status"], "paused")
        self.assertEqual(self.records(), [])

    def test_partial_batch_has_no_receipt_and_recovers_on_retry(self):
        original = module.publish
        calls = 0
        def stop(path, data):
            nonlocal calls
            if calls == 1:
                raise OSError("simulated interruption")
            calls += 1
            original(path, data)
        memory = self.source / "memory.md"
        memory.write_text("Fictional memory", encoding="utf-8")
        with patch.object(module, "publish", side_effect=stop):
            with self.assertRaises(OSError):
                self.run_sync(history=self.history, memory=memory)
        self.assertEqual(self.records("receipts"), [])
        recovered = self.run_sync(history=self.history, memory=memory)
        self.assertEqual((recovered["created"], recovered["duplicates"]), (1, 1))
        receipt = json.loads(self.records("receipts")[0].read_bytes())
        root = self.records("receipts")[0].parent.parent
        for entry in receipt["objects"]:
            self.assertEqual(module.sha((root / entry["path"]).read_bytes()), entry["sha256"])

    def test_tampering_is_preserved_and_refuses_receipt(self):
        self.run_sync(history=self.history)
        target = self.records()[0]
        target.write_bytes(b"Externally changed")
        with self.assertRaises(WorkerError) as error:
            self.run_sync(history=self.history)
        self.assertEqual(error.exception.code, "CONFLICT")
        self.assertEqual(target.read_bytes(), b"Externally changed")

    def test_malformed_export_fails_before_any_content_write(self):
        malformed = []
        cycle = conversation()
        cycle["mapping"]["user"]["parent"] = "answer-a"
        malformed.append(cycle)
        missing = conversation()
        missing["mapping"]["answer-a"]["parent"] = "missing"
        malformed.append(missing)
        current = conversation()
        current["current_node"] = "unknown"
        malformed.append(current)
        malformed.append({"id": "bad", "mapping": {}})
        for value in malformed:
            with self.subTest(value=value):
                self.history.write_text(json.dumps([conversation("valid"), value]), encoding="utf-8")
                with self.assertRaises(WorkerError):
                    self.run_sync(history=self.history)
                self.assertEqual(self.records(), [])

    def test_duplicate_keys_constants_and_truncated_json_rejected(self):
        for raw in [b'[{"id":"a","id":"b"}]', b'[NaN]', b'[{', b'[] garbage', b'[{},]']:
            with self.subTest(raw=raw):
                self.history.write_bytes(raw)
                with self.assertRaises(WorkerError):
                    self.run_sync(history=self.history)
        self.assertEqual(self.records(), [])

    def test_unknown_and_hidden_content_retains_raw_and_reports_limits(self):
        value = conversation()
        value["mapping"]["answer-a"]["message"]["content"] = {"content_type": "unknown", "secret": "RAW_ONLY"}
        hidden = deepcopy(value["mapping"]["answer-b"])
        hidden["id"] = "hidden"
        hidden["message"]["id"] = "hidden-message"
        hidden["message"]["channel"] = "analysis"
        value["mapping"]["hidden"] = hidden
        value["mapping"]["user"]["message"]["content"]["content_type"] = "multimodal_text"
        value["mapping"]["user"]["message"]["content"]["parts"].append({"asset_pointer": "https://invalid.example/no-fetch"})
        self.history.write_text(json.dumps([value]), encoding="utf-8")
        result = self.run_sync(history=self.history)
        self.assertEqual(result["warnings"], {"UNSUPPORTED_CONTENT": 1, "NON_VISIBLE_MESSAGE": 1, "UNSUPPORTED_ATTACHMENT": 1})
        record = json.loads(self.records()[0].read_bytes())
        self.assertIn("RAW_ONLY", record["raw_json"])
        self.assertNotIn("RAW_ONLY", json.dumps(record["normalized"]))

    def test_bounds_quota_and_no_writes(self):
        with patch.object(module, "MAX_JSON", 20):
            with self.assertRaises(WorkerError):
                self.run_sync(history=self.history)
        with patch.object(module, "INBOX_QUOTA", 20):
            with self.assertRaises(WorkerError):
                self.run_sync(history=self.history)
        self.assertEqual(self.records(), [])

    def test_unsafe_ambiguous_zip_history_members_rejected(self):
        for name in ["../conversations.json", "folder/conversations.json", "C:\\conversations.json"]:
            archive = self.source / "export.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr(name, self.history.read_bytes())
            with self.assertRaises(WorkerError):
                self.run_sync(history=archive)
        archive = self.source / "duplicate.zip"
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("conversations.json", self.history.read_bytes())
            with self.assertWarns(UserWarning):
                zipped.writestr("conversations.json", self.history.read_bytes())
        with self.assertRaises(WorkerError):
            self.run_sync(history=archive)

    def test_outside_root_overlapping_roots_and_link_guard(self):
        outside = self.root / "conversations.json"
        outside.write_bytes(self.history.read_bytes())
        with self.assertRaises(WorkerError):
            self.run_sync(history=outside)
        self.configure(inbox_root=str(self.source / "inbox"))
        with self.assertRaises(WorkerError):
            self.run_sync(history=self.history)
        self.configure(inbox_root=str(self.inbox))
        with patch("memory_worker.paths.Path.is_junction", return_value=True):
            with self.assertRaises(WorkerError):
                self.run_sync(history=self.history)

    def test_conflicting_partition_ids_fail_without_writes(self):
        second = conversation()
        second["title"] = "Different revision in same export"
        self.history.write_text(json.dumps([conversation(), second]), encoding="utf-8")
        with self.assertRaises(WorkerError) as error:
            self.run_sync(history=self.history)
        self.assertEqual(error.exception.code, "CONFLICT")
        self.assertEqual(self.records(), [])

    def test_empty_and_all_excluded_are_explicit(self):
        self.history.write_bytes(b"[]")
        self.assertEqual(self.run_sync(history=self.history)["status"], "empty")
        self.history.write_bytes(b"[" + self.raw + b"]")
        self.configure(excluded_conversation_ids=["session-one"])
        self.assertEqual(self.run_sync(history=self.history)["status"], "excluded")
        self.assertFalse(self.inbox.exists())

    def command(self):
        return [sys.executable, "-m", "memory_worker.chatgpt_sync", "--config", str(self.config_path),
                "--history", str(self.history)]

    def test_real_process_restart_and_redacted_cli_error(self):
        first = subprocess.run(self.command(), capture_output=True, timeout=20)
        self.assertEqual(first.returncode, 0, first.stderr)
        second = subprocess.run(self.command(), capture_output=True, timeout=20)
        self.assertEqual(json.loads(second.stdout)["status"], "duplicate")
        self.assertNotIn(b"<script>", first.stdout + first.stderr)
        self.history.write_bytes(b"INVALID_SYNTHETIC_SECRET")
        failed = subprocess.run(self.command(), capture_output=True, timeout=20)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(failed.stdout, b"")
        self.assertNotIn(b"INVALID_SYNTHETIC_SECRET", failed.stderr)
        self.assertNotIn(str(self.root).encode(), failed.stderr)

    def test_real_parallel_processes_publish_once(self):
        children = [subprocess.Popen(self.command(), stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        outputs = []
        try:
            for child in children:
                stdout, stderr = child.communicate(timeout=20)
                self.assertEqual(child.returncode, 0, stderr)
                outputs.append(json.loads(stdout))
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=5)
                for stream in (child.stdout, child.stderr):
                    stream.close()
        self.assertEqual(sorted(output["created"] for output in outputs), [0, 1])
        self.assertEqual(len(self.records()), 1)


if __name__ == "__main__":
    unittest.main()
