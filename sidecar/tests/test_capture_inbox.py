"""Temporary synthetic hook sources; never register hooks or read assistant stores."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from memory_worker import capture_inbox as module
from memory_worker.errors import WorkerError
from memory_worker.paths import filesystem_path


class CaptureInboxTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mp-hook-inbox-")
        self.root = filesystem_path(Path(self.temporary.name))
        self.addCleanup(self.cleanup)
        self.source = self.root / "synthetic-source"
        self.source.mkdir()
        self.inbox = self.root / "global-inbox"
        self.config_path = self.root / "capture.json"
        self.config = {"schema_version": 1, "provider": "claude-code", "enabled": True,
                       "source_root": str(self.source), "inbox_root": str(self.inbox)}
        self.save_config()
        self.transcript = self.source / "session.jsonl"
        self.transcript.write_bytes(b'{"type":"user","text":"fictional"}\r\n')
        self.event = {"session_id": "example-session", "transcript_path": str(self.transcript),
                      "hook_event_name": "SessionStart"}
        self.memory_root = self.source / "memory"
        self.memory_root.mkdir()
        self.memory_data = "# Fictional memory\r\nதமிழ் 🧠\r\n<script>inert</script>".encode()
        (self.memory_root / "MEMORY.md").write_bytes(self.memory_data)
        self.memory_path = self.root / "memory-consent.json"
        self.memory_config = {"schema_version": 1, "provider": "claude-code", "enabled": True,
                              "inbox_root": str(self.inbox), "roots": [str(self.memory_root)]}
        self.save_memory_config()

    def cleanup(self):
        allocated = Path(self.temporary.name).resolve()
        if allocated.parent != Path(tempfile.gettempdir()).resolve() or not allocated.name.startswith("mp-hook-inbox-"):
            raise AssertionError("Unexpected cleanup target")
        target = filesystem_path(allocated)
        if target.exists():
            shutil.rmtree(target)
        self.temporary.cleanup()

    def save_config(self):
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")

    def save_memory_config(self):
        self.memory_path.write_text(json.dumps(self.memory_config), encoding="utf-8")

    def index(self):
        return json.loads((self.inbox / "index.json").read_bytes())

    def test_shared_providers_one_index_and_original_fidelity(self):
        module.run_hook(self.config_path, self.event, self.memory_path)
        module.snapshot_memory(self.config_path, self.memory_path)
        self.config["provider"] = "codex"
        self.save_config()
        module.run_hook(self.config_path, self.event)
        result = module.rebuild_index(self.config_path)
        self.assertEqual((result["sessions"], result["memories"], result["revisions"]), (2, 1, 3))
        index = self.index()
        self.assertTrue(index["derived"])
        memory = next(entry for entry in index["entries"] if entry["kind"] == "memory")
        record = json.loads((self.inbox / memory["path"]).read_bytes())
        self.assertEqual(record["raw_text"].encode(), self.memory_data)
        self.assertFalse(record["decisions_confirmed"])
        self.assertEqual(record["completeness"], "selected_files_only")
        markdown = (self.inbox / "index.md").read_text(encoding="utf-8")
        self.assertNotIn("<script>", markdown)
        self.assertNotIn("fictional", markdown)

    def test_start_stop_end_resume_same_session_immutable_revisions(self):
        module.run_hook(self.config_path, self.event)
        self.assertEqual(module.rebuild_index(self.config_path)["revisions"], 1)
        first = self.index()["entries"][0]
        data = (self.inbox / first["path"]).read_bytes()
        self.transcript.write_bytes(self.transcript.read_bytes() + b'{"type":"assistant","text":"resumed"}\n')
        for event in ("Stop", "SessionEnd", "SessionStart"):
            module.run_hook(self.config_path, {**self.event, "hook_event_name": event})
        indexed = module.rebuild_index(self.config_path)
        self.assertEqual((indexed["sessions"], indexed["revisions"]), (1, 2))
        self.assertEqual((self.inbox / first["path"]).read_bytes(), data)

    def test_index_is_rebuildable_and_idempotent(self):
        module.run_hook(self.config_path, self.event)
        module.rebuild_index(self.config_path)
        original = (self.inbox / "index.json").read_bytes()
        modified = (self.inbox / "index.json").stat().st_mtime_ns
        module.rebuild_index(self.config_path)
        self.assertEqual((self.inbox / "index.json").stat().st_mtime_ns, modified)
        (self.inbox / "index.json").write_bytes(b"damaged derived cache")
        module.rebuild_index(self.config_path)
        self.assertEqual((self.inbox / "index.json").read_bytes(), original)

    def test_tampered_snapshot_fails_before_index_replacement(self):
        module.run_hook(self.config_path, self.event)
        module.rebuild_index(self.config_path)
        original = (self.inbox / "index.json").read_bytes()
        target = self.inbox / self.index()["entries"][0]["path"]
        manifest = json.loads(target.read_bytes())
        chunk = self.inbox / "objects" / "chunks" / (manifest["chunks"][0]["sha256"] + ".jsonl")
        chunk.write_bytes(chunk.read_bytes() + b"tampered")
        with self.assertRaises(WorkerError):
            module.rebuild_index(self.config_path)
        self.assertEqual((self.inbox / "index.json").read_bytes(), original)
        self.assertTrue(chunk.read_bytes().endswith(b"tampered"))

    def test_manifest_chunks_preserve_record_boundaries_and_exact_bytes(self):
        first = json.dumps({"text": "a" * 40000}, separators=(",", ":")).encode() + b"\n"
        second = json.dumps({"text": "b" * 40000}, separators=(",", ":")).encode() + b"\n"
        raw = first + second
        self.transcript.write_bytes(raw)
        module.run_hook(self.config_path, self.event)
        module.rebuild_index(self.config_path)
        entry = self.index()["entries"][0]
        target = self.inbox / entry["path"]
        manifest, restored = module.read_session_snapshot(target, "claude-code", entry["key"])
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(len(manifest["chunks"]), 2)
        self.assertEqual(restored, raw)
        for item in manifest["chunks"]:
            chunk = self.inbox / "objects" / "chunks" / (item["sha256"] + ".jsonl")
            self.assertTrue(chunk.read_bytes().endswith(b"\n"))

    def test_tampered_spool_fails_before_canonical_publication(self):
        module.run_hook(self.config_path, self.event)
        spool = next((self.inbox / "spool").rglob("*.json"))
        spool.write_bytes(b'{"transcript":"changed"}')
        with self.assertRaises(WorkerError):
            module.rebuild_index(self.config_path)
        self.assertEqual(spool.read_bytes(), b'{"transcript":"changed"}')
        self.assertFalse((self.inbox / "index.json").exists())

    def test_paused_capture_does_not_read_memory_or_index(self):
        self.config["enabled"] = False
        self.save_config()
        with patch.object(module, "snapshot_memory", side_effect=AssertionError("must not read")):
            self.assertEqual(module.run_hook(self.config_path, self.event, self.memory_path)["status"], "paused")
        self.assertEqual(module.rebuild_index(self.config_path)["status"], "paused")
        self.assertFalse(self.inbox.exists())

    def test_memory_scope_inbox_link_and_provider_mismatch_fail(self):
        self.memory_config["roots"] = [str(self.inbox)]
        self.save_memory_config()
        with self.assertRaises(WorkerError):
            module.snapshot_memory(self.config_path, self.memory_path)
        self.memory_config["roots"] = [str(self.memory_root)]
        self.memory_config["provider"] = "codex"
        self.save_memory_config()
        with self.assertRaises(WorkerError):
            module.snapshot_memory(self.config_path, self.memory_path)
        self.memory_config["provider"] = "claude-code"
        self.save_memory_config()
        with patch("memory_worker.paths.Path.is_junction", return_value=True):
            with self.assertRaises(WorkerError):
                module.snapshot_memory(self.config_path, self.memory_path)

    def test_memory_revisions_duplicate_pause_missing_and_bounds(self):
        self.assertEqual(module.snapshot_memory(self.config_path, self.memory_path)["created"], 1)
        self.assertEqual(module.snapshot_memory(self.config_path, self.memory_path)["created"], 0)
        (self.memory_root / "MEMORY.md").write_text("Fictional revised memory", encoding="utf-8")
        self.assertEqual(module.snapshot_memory(self.config_path, self.memory_path)["created"], 1)
        self.assertEqual(module.rebuild_index(self.config_path)["memories"], 1)
        self.assertEqual(module.rebuild_index(self.config_path)["revisions"], 2)
        with patch.object(module, "MAX_MEMORY", 1):
            with self.assertRaises(WorkerError):
                module.snapshot_memory(self.config_path, self.memory_path)
        self.memory_config["enabled"] = False
        self.save_memory_config()
        self.assertEqual(module.snapshot_memory(self.config_path, self.memory_path)["status"], "paused")
        self.memory_config.update(enabled=True, roots=[str(self.source / "not-created")])
        self.save_memory_config()
        self.assertEqual(module.snapshot_memory(self.config_path, self.memory_path)["status"], "unavailable")

    def test_index_scan_limits_fail_without_index(self):
        module.run_hook(self.config_path, self.event)
        with patch.object(module, "MAX_INDEX_SCAN", 1):
            with self.assertRaises(WorkerError):
                module.rebuild_index(self.config_path)
        self.assertFalse((self.inbox / "index.json").exists())

    def test_real_hook_process_empty_stdout_and_separate_index_command(self):
        command = [sys.executable, str(Path(__file__).resolve().parents[2] / "tools/capture-hook.py"), "--config", str(self.config_path)]
        self.process_flow(command)

    @unittest.skipUnless(os.environ.get("MP_CAPTURE_EXECUTABLE"), "Frozen capture executable not selected")
    def test_frozen_hook_memory_and_index_process(self):
        command = [os.environ["MP_CAPTURE_EXECUTABLE"], "--config", str(self.config_path)]
        self.process_flow(command)

    def process_flow(self, command):
        child = subprocess.run(command,
                               input=json.dumps(self.event).encode(), capture_output=True, timeout=20, cwd=self.source)
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertEqual(child.stdout, b"")
        self.assertNotIn(b"fictional", child.stderr)
        self.assertFalse((self.inbox / "index.json").exists())
        indexed = subprocess.run(command + ["--rebuild-index", "--memory-config", str(self.memory_path)], capture_output=True, timeout=20, cwd=self.source)
        self.assertEqual(indexed.returncode, 0, indexed.stderr)
        self.assertEqual(indexed.stdout, b"")
        entries = self.index()["entries"]
        self.assertEqual(len(entries), 2)
        session = next(item for item in entries if item["kind"] == "session")
        manifest, restored = module.read_session_snapshot(self.inbox / session["path"], "claude-code", session["key"])
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(restored, self.transcript.read_bytes())


if __name__ == "__main__":
    unittest.main()
