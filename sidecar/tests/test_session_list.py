import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import nullcontext
from unittest.mock import patch

from memory_worker.errors import WorkerError
from memory_worker.vault import Vault
from test_foundation import call, op, ROOT


class SessionListTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mp-session-list-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "vault"
        self.vault = Vault(self.root, True)

    def create(self, title="Synthetic", timestamp=None):
        context = patch("memory_worker.vault.now", return_value=timestamp) if timestamp else nullcontext()
        with context:
            return call(self.vault, "sessions.create", op_id=op(), title=title, body="Summary", source_text="Original\r\nதமிழ்")["id"]

    def test_empty_and_reopened_metadata_only(self):
        self.assertEqual(call(self.vault, "sessions.list", limit=50, offset=0), {"items": [], "total": 0, "next_offset": None})
        record_id = self.create()
        listed = call(Vault(self.root), "sessions.list", limit=50, offset=0)
        self.assertEqual(listed["items"][0]["id"], record_id)
        self.assertNotIn("source_text", listed["items"][0])
        self.assertNotIn("body", listed["items"][0])
        self.assertEqual(call(Vault(self.root), "sessions.read", id=record_id)["source_text"], "Original\r\nதமிழ்")

    def test_pagination_calendar_order_and_ties(self):
        oldest = self.create("Older", "2026-10-02T12:00:00Z")
        newer = self.create("Newer", "2026-10-02T12:00:00.1Z")
        tied = self.create("Tied", "2026-10-02T12:00:00.100000Z")
        expected = sorted([newer, tied], reverse=True) + [oldest]
        ids = []
        for offset in range(3):
            result = call(self.vault, "sessions.list", limit=1, offset=offset)
            ids.append(result["items"][0]["id"])
            self.assertEqual(result["next_offset"], offset + 1 if offset < 2 else None)
            self.assertEqual(result["total"], 3)
        self.assertEqual(ids, expected)
        self.assertEqual(call(self.vault, "sessions.list", limit=10, offset=1000)["items"], [])

    def test_invalid_pagination_and_unknown_method(self):
        for params in [{"limit": 0, "offset": 0}, {"limit": 51, "offset": 0}, {"limit": 1, "offset": -1},
                       {"limit": 1, "offset": 1001}, {"limit": True, "offset": 0}, {"limit": 1},
                       {"limit": 1, "offset": 0, "path": "elsewhere"}]:
            with self.assertRaises(WorkerError):
                call(self.vault, "sessions.list", **params)
        with self.assertRaises(WorkerError):
            self.vault.call("not.allowed", {})

    def test_invalid_metadata_is_reported_without_alteration(self):
        record_id = self.create()
        path = self.root / "sessions" / (record_id + ".md")
        original = path.read_bytes()
        start, front, rest = original.split(b"\n", 2)
        metadata = json.loads(front)
        for changes in [{"created_at": "2026-02-30T12:00:00Z"}, {"created_at": "0000-10-02T12:00:00Z"},
                        {"created_at": "2026-12-31T23:59:60Z"}, {"id": op()}, {"decision_state": "confirmed"}]:
            damaged = start + b"\n" + json.dumps({**metadata, **changes}).encode() + b"\n" + rest
            path.write_bytes(damaged)
            with self.assertRaises(WorkerError):
                call(self.vault, "sessions.list", limit=50, offset=0)
            self.assertEqual(path.read_bytes(), damaged)
        duplicated = start + b'\n{"title":"other",' + front[1:] + b"\n" + rest
        path.write_bytes(duplicated)
        with self.assertRaises(WorkerError):
            call(self.vault, "sessions.list", limit=50, offset=0)
        path.write_bytes(original)

    def test_listing_does_not_read_source_contents(self):
        record_id = self.create()
        loaded = call(self.vault, "sessions.read", id=record_id)
        source = self.root / "sources" / loaded["metadata"]["source_id"] / "original.txt"
        source.write_bytes(b"Changed externally")
        self.assertEqual(call(self.vault, "sessions.list", limit=50, offset=0)["total"], 1)
        # Metadata listing is not a source-integrity certification; opening is.
        with self.assertRaises(WorkerError) as error:
            call(self.vault, "sessions.read", id=record_id)
        self.assertEqual(error.exception.code, "CONFLICT")

    def test_header_size_and_unexpected_entries_fail_closed(self):
        record_id = self.create()
        path = self.root / "sessions" / (record_id + ".md")
        original = path.read_bytes()
        path.write_bytes(b"---\n" + b"x" * 8192 + b"\n---\n")
        with self.assertRaises(WorkerError):
            call(self.vault, "sessions.list", limit=50, offset=0)
        path.write_bytes(original)
        (path.parent / "unrecognized.md").write_bytes(b"User file")
        with self.assertRaises(WorkerError):
            call(self.vault, "sessions.list", limit=50, offset=0)
        self.assertEqual((path.parent / "unrecognized.md").read_bytes(), b"User file")

    def test_inventory_limit_is_bounded(self):
        directory = self.root / "sessions"
        directory.mkdir()
        for _ in range(1001):
            (directory / (op() + ".md")).touch()
        metadata = {"id": op(), "created_at": "2026-10-02T12:00:00Z"}
        with patch.object(self.vault, "session_header", return_value=metadata) as header:
            with self.assertRaises(WorkerError) as error:
                call(self.vault, "sessions.list", limit=1, offset=0)
            self.assertEqual(error.exception.code, "LIMIT_EXCEEDED")
            self.assertEqual(header.call_count, 1000)

    def test_ask_returns_exact_verified_evidence_and_abstains(self):
        matching = call(self.vault, "sessions.create", op_id=op(), title="Database choice", body="",
                        source_text='{"role":"user","text":"Which database?"}\n'
                                    '{"role":"assistant","text":"We chose SQLite for the local vault."}\n')["id"]
        self.create("Unrelated")
        result = call(self.vault, "sessions.ask", question="Which database did we choose?")
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["sources"][0]["session_id"], matching)
        self.assertIn("SQLite", result["answer"])
        source = result["sources"][0]
        stored = call(self.vault, "sessions.read", id=matching)["source_text"]
        self.assertEqual(stored[source["start"]:source["end"]], source["quote"])
        missing = call(self.vault, "sessions.ask", question="What was the zephyrquartz plan?")
        self.assertEqual(missing["status"], "insufficient_evidence")
        self.assertEqual(missing["sources"], [])

    def process_flow(self, command):
        record_id = self.create()
        environment = {key: value for key, value in os.environ.items() if key.upper() in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP")}
        environment["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
        if len(command) > 1:
            environment["PYTHONPATH"] = str(ROOT / "sidecar")
        request = {"protocol_version": 1, "id": "list", "method": "sessions.list", "params": {"limit": 50, "offset": 0}}
        child = subprocess.run(command + ["--mode", "ui", "--vault", str(self.root)],
                               input=(json.dumps(request) + "\n").encode(), capture_output=True, env=environment, timeout=30)
        self.assertEqual(child.returncode, 0)
        self.assertEqual(child.stderr, b"")
        response = json.loads(child.stdout)
        self.assertEqual(response["id"], "list")
        self.assertEqual(response["result"]["items"][0]["id"], record_id)

    def test_source_process_list(self):
        self.process_flow([sys.executable, "-m", "memory_worker"])

    @unittest.skipUnless(os.environ.get("MP_FROZEN_WORKER"), "Frozen worker not selected")
    def test_frozen_process_list(self):
        self.process_flow([os.environ["MP_FROZEN_WORKER"]])


if __name__ == "__main__":
    unittest.main()
