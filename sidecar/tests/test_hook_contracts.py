import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from memory_worker.capture_inbox import read_session_snapshot, rebuild_index


FIXTURES = Path(__file__).with_name("fixtures")
RECEIVER = Path(__file__).resolve().parents[2] / "tools" / "capture-hook.py"
EXPECTED_EVENTS = {"SessionStart", "Stop", "SessionEnd"}


def load_fixture(name: str) -> dict[str, object]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("fixture must be an object")
    return value


class HookContractTests(unittest.TestCase):
    def run_fixture(self, name: str) -> None:
        fixture = load_fixture(name)
        self.assertEqual(fixture["schema_version"], 1)
        self.assertEqual(fixture["transcript_contract"], "opaque_jsonl")
        provider = fixture["provider"]
        self.assertIn(provider, {"codex", "claude-code"})
        lines = fixture["transcript_lines"]
        events = fixture["events"]
        self.assertIsInstance(lines, list)
        self.assertIsInstance(events, list)
        raw = ("\n".join(lines) + "\n").encode("utf-8")

        with tempfile.TemporaryDirectory(prefix="mp-hook-contract-") as directory:
            root = Path(directory)
            source = root / "source"
            inbox = root / "inbox"
            source.mkdir()
            transcript = source / "session.jsonl"
            transcript.write_bytes(raw)
            config = root / "consent.json"
            config.write_text(json.dumps({
                "schema_version": 1,
                "provider": provider,
                "enabled": True,
                "source_root": str(source),
                "inbox_root": str(inbox),
            }), encoding="utf-8")
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(RECEIVER.parents[1] / "sidecar")

            seen: set[str] = set()
            for template in events:
                self.assertIsInstance(template, dict)
                event = dict(template)
                event["transcript_path"] = str(transcript)
                seen.add(event["hook_event_name"])
                completed = subprocess.run(
                    [sys.executable, str(RECEIVER), "--config", str(config)],
                    input=json.dumps(event, ensure_ascii=False).encode("utf-8"),
                    capture_output=True,
                    env=environment,
                    timeout=10,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(completed.stdout, b"")
                self.assertNotIn(b"Synthetic event metadata", completed.stderr)

            self.assertEqual(seen, EXPECTED_EVENTS)
            spooled = list((inbox / "spool" / provider).glob("*.json"))
            self.assertEqual(len(spooled), len(events))
            rebuilt = rebuild_index(config)
            self.assertEqual((rebuilt["sessions"], rebuilt["revisions"]), (1, 1))
            self.assertEqual(list((inbox / "spool" / provider).glob("*.json")), [])
            records = list(inbox.glob(f"{provider}/*/*.json"))
            self.assertEqual(len(records), 1)
            record, restored = read_session_snapshot(records[0], provider, records[0].parent.name)
            self.assertEqual(record["provider"], provider)
            self.assertEqual(record["schema_version"], 2)
            self.assertEqual(restored, raw)
            self.assertEqual(record["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertFalse(record["normalized"])
            self.assertNotIn("last_assistant_message", record)
            self.assertNotIn("future_field", record)

    def test_codex_lifecycle_fixture_is_captured_as_opaque_jsonl(self):
        self.run_fixture("codex-hook-events.json")

    def test_claude_code_lifecycle_fixture_is_captured_as_opaque_jsonl(self):
        self.run_fixture("claude-code-hook-events.json")


if __name__ == "__main__":
    unittest.main()
