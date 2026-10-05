import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from memory_worker.capture_control import dispatch
from memory_worker.capture_inbox import run_hook
from memory_worker.errors import WorkerError


class CaptureControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mp-control-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "app-capture"
        self.source = self.base / "synthetic-source"
        self.source.mkdir()
        self.memory = self.base / "synthetic-memory"
        self.memory.mkdir()
        self.exe = Path(os.environ.get("MP_CAPTURE_EXECUTABLE", self.base / "receiver.exe"))

    def status(self):
        return dispatch(self.root, {"method": "status"}, self.exe)

    def request(self, provider="codex", **changes):
        current = next(item for item in self.status()["clients"] if item["provider"] == provider)
        return {"method": "configure", "provider": provider, "source_root": str(self.source),
                "memory_roots": [], "enabled": False, "memory_enabled": False,
                "revision": current["revision"], **changes}

    def test_readonly_defaults_and_explicit_scope_no_settings_changes(self):
        value = self.status()
        self.assertFalse(self.root.exists())
        self.assertEqual(len(value["clients"]), 2)
        self.assertTrue(all(not item["enabled"] for item in value["clients"]))
        dispatch(self.root, self.request(), self.exe)
        self.assertEqual(list(self.source.iterdir()), [])
        self.assertFalse(self.status()["clients"][1]["enabled"])
        hook = json.loads(self.status()["clients"][1]["snippet"])
        self.assertEqual(set(hook["hooks"]), {"SessionStart", "Stop", "SessionEnd"})
        self.assertEqual(hook["hooks"]["SessionEnd"][0]["hooks"][0]["timeout"], 3)

    def test_consent_pause_conflict_and_shared_index_originals(self):
        transcript = self.source / "session.jsonl"
        transcript.write_bytes(b'{"type":"synthetic","text":"inert"}\n')
        (self.memory / "MEMORY.md").write_text("# Synthetic unreviewed", encoding="utf-8")
        request = self.request(enabled=True, memory_enabled=True, memory_roots=[str(self.memory)])
        dispatch(self.root, request, self.exe)
        config = self.root / "settings/codex.json"
        memory = self.root / "settings/codex-memory.json"
        event = {"session_id": "synthetic", "hook_event_name": "Stop", "transcript_path": str(transcript)}
        self.assertEqual(run_hook(config, event, memory)["status"], "captured")
        with self.assertRaises(WorkerError):
            dispatch(self.root, request, self.exe)  # stale scope cannot overwrite
        before = list((self.root / "inbox/codex").rglob("*.json"))
        dispatch(self.root, self.request(enabled=False), self.exe)
        self.assertEqual(run_hook(config, event, memory)["status"], "paused")
        self.assertEqual(before, list((self.root / "inbox/codex").rglob("*.json")))
        result = dispatch(self.root, {"method": "index"}, self.exe)
        self.assertEqual((result["sessions"], result["memories"], result["revisions"]), (1, 0, 1))
        index = (self.root / "inbox/index.md").read_text()
        self.assertNotIn("# Synthetic unreviewed", index)

    def test_reject_unknown_fields_overlapping_scopes_and_bad_memory_consent(self):
        for extra in ({"endpoint": "remote"}, {"source_root": str(self.root.parent)},
                      {"memory_enabled": True}, {"enabled": 1},
                      {"memory_roots": [str(self.memory), str(self.memory / "nested")]}):
            with self.subTest(extra=extra), self.assertRaises((WorkerError, TypeError)):
                dispatch(self.root, self.request(**extra), self.exe)
        self.assertFalse(self.root.exists())
        bad = self.request()
        bad["provider"] = []
        with self.assertRaises(WorkerError):
            dispatch(self.root, bad, self.exe)

    def test_preserve_tampered_config_and_pause_missing_source(self):
        dispatch(self.root, self.request(enabled=True), self.exe)
        self.source.rmdir()
        self.assertTrue(self.status()["clients"][1]["enabled"])
        dispatch(self.root, self.request(enabled=False), self.exe)
        target = self.root / "settings/codex.json"
        target.write_text('{"unexpected":"private"}')
        with self.assertRaises(WorkerError):
            self.status()
        self.assertEqual(target.read_text(), '{"unexpected":"private"}')

    def test_codex_hook_merge_backup_and_remove_preserve_user_handlers(self):
        dispatch(self.root, self.request(enabled=True), self.exe)
        codex_home = self.base / "codex-home"
        codex_home.mkdir()
        hook_path = codex_home / "hooks.json"
        existing = {"description": "User hooks", "hooks": {"Stop": [
            {"hooks": [{"type": "command", "command": "echo existing", "timeout": 4}]}]}}
        hook_path.write_text(json.dumps(existing), encoding="utf-8")
        def hook(action):
            return dispatch(self.root, {"method": "codex-hook", "action": action,
                                        "codex_home": str(codex_home)}, self.exe)
        self.assertEqual(hook("status")["status"], "absent")
        self.assertEqual(hook("install")["status"], "installed")
        self.assertEqual(hook("install")["status"], "installed")
        installed = json.loads(hook_path.read_text(encoding="utf-8"))
        self.assertEqual(len(installed["hooks"]["Stop"]), 2)
        self.assertEqual(installed["hooks"]["Stop"][0], existing["hooks"]["Stop"][0])
        self.assertFalse(hook("status")["trust_verified"])
        backups = list((self.root / "settings/codex-hooks-backups").glob("*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(json.loads(backups[0].read_text()), existing)
        self.assertEqual(hook("remove")["status"], "absent")
        removed = json.loads(hook_path.read_text(encoding="utf-8"))
        self.assertEqual(removed["description"], "User hooks")
        self.assertEqual(removed["hooks"]["Stop"], existing["hooks"]["Stop"])
        self.assertEqual(len(list((self.root / "settings/codex-hooks-backups").glob("*.json"))), 2)

    def test_codex_hook_refuses_inline_hooks_without_changing_files(self):
        dispatch(self.root, self.request(enabled=True), self.exe)
        codex_home = self.base / "codex-inline"
        codex_home.mkdir()
        (codex_home / "config.toml").write_text("[hooks]\n", encoding="utf-8")
        with self.assertRaises(WorkerError):
            dispatch(self.root, {"method": "codex-hook", "action": "install",
                                 "codex_home": str(codex_home)}, self.exe)
        self.assertFalse((codex_home / "hooks.json").exists())

    def test_codex_hook_preserves_persisted_trust_during_reinstall(self):
        dispatch(self.root, self.request(enabled=True), self.exe)
        codex_home = self.base / "codex-trusted"
        codex_home.mkdir()
        config = codex_home / "config.toml"
        original = b'[hooks.state."user-hook"]\ntrusted_hash = "sha256:existing"\nenabled = true\n'
        config.write_bytes(original)
        request = {"method": "codex-hook", "codex_home": str(codex_home)}
        for action in ["install", "remove", "install"]:
            result = dispatch(self.root, {**request, "action": action}, self.exe)
            self.assertEqual(result["status"], "absent" if action == "remove" else "installed")
            self.assertEqual(config.read_bytes(), original)
        config.write_bytes(original + b'\n[[hooks.Stop]]\nhooks = []\n')
        dispatch(self.root, {**request, "action": "remove"}, self.exe)
        with self.assertRaises(WorkerError):
            dispatch(self.root, {**request, "action": "install"}, self.exe)
        self.assertEqual(config.read_bytes(), original + b'\n[[hooks.Stop]]\nhooks = []\n')

    def test_codex_direct_tokens_exclude_shell_metacharacters(self):
        from memory_worker.capture_control import snippets
        import base64
        safe = Path("C:/safe/memory-capture.exe")
        config = Path("C:/safe/codex.json")
        command = json.loads(snippets("codex", safe, config, config))["hooks"]["SessionEnd"][0]["hooks"][0]["command"]
        self.assertEqual(command, str(safe) + " --config " + str(config))
        for character in [" ", "'", "$", "%", "&", ";", "(", ")"]:
            path = Path("C:/scope" + character + "literal/codex.json")
            command = json.loads(snippets("codex", safe, path, path))["hooks"]["SessionEnd"][0]["hooks"][0]["command"]
            self.assertTrue(command.startswith("powershell.exe -NoProfile -NonInteractive -EncodedCommand "))
            script = base64.b64decode(command.split()[-1]).decode("utf-16le")
            self.assertIn("'" + str(path).replace("'", "''") + "'", script)

    def test_app_control_dispatches_a_frame_without_waiting_for_stdin_eof(self):
        command = [str(self.exe)] if os.environ.get('MP_CAPTURE_EXECUTABLE') else [
            sys.executable, str(Path(__file__).resolve().parents[2] / 'tools/capture-hook.py')]
        process = subprocess.Popen([*command, '--app-control-root', str(self.root)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            process.stdin.write(b'{"method":"status"}\n')
            process.stdin.flush()
            # The input pipe stays open through process completion.
            self.assertEqual(process.wait(timeout=10), 0)
            value = json.loads(process.stdout.read())
            self.assertEqual(value['schema_version'], 1)
            self.assertEqual(len(value['clients']), 2)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()
            process.stderr.close()

    @unittest.skipUnless(os.environ.get("MP_CAPTURE_EXECUTABLE"), "Frozen receiver not selected")
    def test_actual_frozen_app_control_and_generated_codex_command(self):
        self.root = self.base / "app capture O'Neil $literal"
        def control(request):
            completed = subprocess.run([str(self.exe), "--app-control-root", str(self.root)],
                                       input=json.dumps(request).encode(), capture_output=True,
                                       cwd=self.source, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            return json.loads(completed.stdout)
        self.assertEqual(control({"method": "status"}), self.status())
        value = control(self.request(enabled=True))
        codex_home = self.base / "frozen-trusted"
        codex_home.mkdir()
        config = codex_home / "config.toml"
        trusted = b'[hooks.state."user-hook"]\ntrusted_hash = "sha256:existing"\n'
        config.write_bytes(trusted)
        for action in ["install", "remove", "install"]:
            result = control({"method": "codex-hook", "action": action, "codex_home": str(codex_home)})
            self.assertEqual(result["status"], "absent" if action == "remove" else "installed")
            self.assertEqual(config.read_bytes(), trusted)
        command = json.loads(value["clients"][1]["snippet"])["hooks"]["Stop"][0]["hooks"][0]["command"]
        transcript = self.source / "session.jsonl"
        transcript.write_bytes(b'{"type":"synthetic"}\n')
        event = {"session_id": "synthetic", "hook_event_name": "Stop", "transcript_path": str(transcript)}
        completed = subprocess.run(command, input=json.dumps(event).encode(), capture_output=True,
                                   cwd=self.source, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, b"")
        self.assertEqual(control({"method": "index"})["sessions"], 1)
        self.assertTrue((self.root / "inbox/index.json").exists())
        value = control(self.request(provider="claude-code", enabled=True))
        handler = json.loads(value["clients"][0]["snippet"])["hooks"]["Stop"][0]["hooks"][0]
        completed = subprocess.run([handler["command"], *handler["args"]],
                                   input=json.dumps(event).encode(), capture_output=True,
                                   cwd=self.source, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, b"")
        self.assertEqual(control({"method": "index"})["sessions"], 2)


if __name__ == "__main__":
    unittest.main()
