import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from memory_worker.errors import WorkerError
from memory_worker.session_capture import capture, configuration, read_transcript, MAX_EVENT


class CaptureTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="mp-capture-synthetic-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "synthetic-assistant"
        self.source.mkdir()
        self.inbox = self.root / "synthetic-inbox"
        self.config_path = self.root / "consent.json"
        self.config = {"schema_version": 1, "provider": "codex", "enabled": True,
                       "source_root": str(self.source), "inbox_root": str(self.inbox)}
        self.save_config()
        self.transcript = self.source / "example.jsonl"
        self.raw = '{"example":"தமிழ் 😀 <script>data only</script>"}\r\n'.encode()
        self.transcript.write_bytes(self.raw)
        self.event = {"hook_event_name": "Stop", "session_id": "synthetic-123",
                      "transcript_path": str(self.transcript), "cwd": str(self.source)}

    def save_config(self):
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")

    def records(self):
        return list(self.inbox.rglob("*.json"))

    def run_hook(self, event):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        return subprocess.run([sys.executable, "-m", "memory_worker.session_capture",
                               "--config", str(self.config_path)],
                              input=json.dumps(event).encode(), capture_output=True,
                              env=env, timeout=10)

    def test_exact_bytes_and_duplicate_across_process_restart(self):
        first = self.run_hook(self.event)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, b"")
        self.assertNotIn("தமிழ்".encode(), first.stderr)
        paths = self.records()
        self.assertEqual(len(paths), 1)
        stored = json.loads(paths[0].read_bytes())
        self.assertEqual(stored["transcript"].encode(), self.raw)
        self.assertEqual(stored["sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertFalse(stored["normalized"])
        prior = paths[0].read_bytes()
        second = self.run_hook(self.event)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn(b"duplicate", second.stderr)
        self.assertEqual(paths[0].read_bytes(), prior)

    def test_append_and_resume_keep_identity_and_original_snapshot(self):
        first = capture(self.config_path, self.event)
        original = self.records()[0].read_bytes()
        self.transcript.write_bytes(self.raw + b'{"example":"later"}\n')
        self.event["hook_event_name"] = "SessionStart"
        later = capture(self.config_path, self.event)
        self.assertEqual(first["session_key"], later["session_key"])
        self.assertNotEqual(first["sha256"], later["sha256"])
        self.assertEqual(len(self.records()), 2)
        self.assertIn(original, [p.read_bytes() for p in self.records()])

    def test_claude_provider_is_separate_from_codex(self):
        codex = capture(self.config_path, self.event)
        self.config["provider"] = "claude-code"
        self.save_config()
        claude = capture(self.config_path, self.event)
        self.assertNotEqual(codex["session_key"], claude["session_key"])
        self.assertEqual(len(self.records()), 2)

    def test_partial_tail_is_not_archived_until_complete(self):
        self.transcript.write_bytes(self.raw + b'{"pending":')
        result = capture(self.config_path, self.event)
        self.assertTrue(result["partial_tail"])
        self.assertEqual(json.loads(self.records()[0].read_bytes())["transcript"].encode(), self.raw)
        self.transcript.write_bytes(self.raw + b'{"pending":true}\n')
        self.assertFalse(capture(self.config_path, self.event)["partial_tail"])
        self.assertEqual(len(self.records()), 2)

    def test_empty_and_partial_only_wait_without_inbox(self):
        for content in (b"", b'{"pending":'):
            self.transcript.write_bytes(content)
            self.assertEqual(capture(self.config_path, self.event)["status"], "waiting")
            self.assertFalse(self.inbox.exists())

    def test_pause_prevents_source_read_and_content_writes(self):
        self.config["enabled"] = False
        self.save_config()
        self.transcript.unlink()
        self.assertEqual(capture(self.config_path, self.event), {"status": "paused"})
        self.assertFalse(self.inbox.exists())

    def test_pause_during_read_is_rechecked_before_persistence(self):
        def pause(value, source):
            result = read_transcript(value, source)
            self.config["enabled"] = False
            self.save_config()
            return result
        with patch("memory_worker.session_capture.read_transcript", side_effect=pause):
            self.assertEqual(capture(self.config_path, self.event)["status"], "paused")
        self.assertEqual(self.records(), [])

    def test_simultaneous_hook_processes_deduplicate(self):
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
        command = [sys.executable, "-m", "memory_worker.session_capture", "--config", str(self.config_path)]
        children = [subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, env=env) for _ in range(2)]
        try:
            for child in children:
                child.stdin.write(json.dumps(self.event).encode())
                child.stdin.close()
                child.stdin = None
            for child in children:
                stdout, stderr = child.communicate(timeout=15)
                self.assertEqual(child.returncode, 0, stderr)
                self.assertEqual(stdout, b"")
            self.assertEqual(len(self.records()), 1)
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=5)
                if child.stdout is not None:
                    child.stdout.close()
                if child.stderr is not None:
                    child.stderr.close()

    def test_scope_escape_and_link_are_rejected(self):
        outside = self.root / "outside.jsonl"
        outside.write_bytes(self.raw)
        self.event["transcript_path"] = str(outside)
        with self.assertRaises(WorkerError):
            capture(self.config_path, self.event)
        self.event["transcript_path"] = str(self.transcript)
        # Exercise the same guard without requiring Windows symlink privileges.
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaises(WorkerError):
                capture(self.config_path, self.event)
        self.assertFalse(self.inbox.exists())

    def test_complete_malformed_records_fail_not_empty_success(self):
        for raw in (b'{bad}\n', b'[]\n', b'{"x":1,"x":2}\n', b'{"x":NaN}\n', b'{"x":"\xff"}\n'):
            self.transcript.write_bytes(raw)
            with self.assertRaises(WorkerError):
                capture(self.config_path, self.event)
        self.assertFalse(self.inbox.exists())

    def test_configuration_must_be_explicit_and_strict(self):
        for change in ({"enabled": "yes"}, {"provider": "chatgpt"},
                       {"extra": True}, {"inbox_root": str(self.source / "nested")},
                       {"source_root": "relative"}):
            self.config = {"schema_version": 1, "provider": "codex", "enabled": True,
                           "source_root": str(self.source), "inbox_root": str(self.inbox)}
            self.config.update(change)
            self.save_config()
            with self.assertRaises(WorkerError):
                configuration(self.config_path)
        self.assertFalse(self.inbox.exists())

    def test_unavailable_transcript_and_unsupported_event(self):
        self.event["transcript_path"] = None
        self.assertEqual(capture(self.config_path, self.event)["status"], "unavailable")
        self.event["hook_event_name"] = "Unknown"
        with self.assertRaises(WorkerError):
            capture(self.config_path, self.event)

    def test_oversized_input_and_transcript_are_rejected_redacted(self):
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
        run = subprocess.run([sys.executable, "-m", "memory_worker.session_capture",
                              "--config", str(self.config_path)], input=b"a" * (MAX_EVENT + 1),
                             capture_output=True, env=env, timeout=10)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(run.stdout, b"")
        self.assertIn(b"LIMIT_EXCEEDED", run.stderr)
        with patch("memory_worker.session_capture.MAX_TRANSCRIPT", 8):
            with self.assertRaises(WorkerError):
                capture(self.config_path, self.event)

    def test_tampered_duplicate_is_preserved_and_reported(self):
        capture(self.config_path, self.event)
        path = self.records()[0]
        path.write_bytes(b'{"transcript":"changed"}')
        with self.assertRaises(WorkerError):
            capture(self.config_path, self.event)
        self.assertEqual(path.read_bytes(), b'{"transcript":"changed"}')


if __name__ == "__main__":
    unittest.main()
