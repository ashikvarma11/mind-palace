"""Isolated real Codex hook trust probe; no bypass or account credentials."""
from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer

import runpy
import re
import argparse

ROOT = Path(__file__).resolve().parents[1]
CODEX = Path(os.environ["CODEX_CLI_PATH"])
Fixture = runpy.run_path(str(ROOT / "tools/verify-codex-client.py"))["Fixture"]
sys.path.insert(0, str(ROOT / "sidecar"))
from memory_worker.capture_control import dispatch
from memory_worker.service import dispatch as vault_dispatch
from memory_worker.vault import Vault


def hooks_list(environment: dict[str, str], workspace: Path) -> list[dict]:
    child = subprocess.Popen([str(CODEX), "app-server", "--stdio"], cwd=workspace,
        env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8")
    messages: queue.Queue = queue.Queue()
    def read() -> None:
        for line in child.stdout:
            messages.put(json.loads(line))
    threading.Thread(target=read, daemon=True).start()
    def request(identifier: int, method: str, params: dict) -> dict:
        child.stdin.write(json.dumps({"id": identifier, "method": method, "params": params}) + "\n")
        child.stdin.flush()
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            message = messages.get(timeout=max(0.01, deadline - time.monotonic()))
            if message.get("id") == identifier:
                if "error" in message:
                    raise RuntimeError("Installed app-server request failed: " + method)
                return message["result"]
        raise RuntimeError("Installed app-server request timed out: " + method)
    try:
        request(1, "initialize", {"clientInfo": {"name": "mind_palace_trust_probe", "version": "1"},
            "capabilities": {"experimentalApi": True}})
        child.stdin.write('{"method":"initialized"}\n')
        child.stdin.flush()
        result = request(2, "hooks/list", {"cwds": [str(workspace)]})
        return [hook for entry in result["data"] for hook in entry["hooks"]]
    finally:
        child.stdin.close()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume-probe", type=Path)
    parser.add_argument("--existing-session", help="Finish checks on an already verified synthetic two-turn client run")
    args = parser.parse_args()
    base = ROOT / ".tools/codex-hook-probe"
    allocated = args.resume_probe.resolve() if args.resume_probe else Path(tempfile.mkdtemp(prefix="trust-", dir=base))
    if allocated.parent != base.resolve() or not allocated.name.startswith("trust-"):
        raise RuntimeError("Only owned synthetic trust probes can be resumed")
    home = allocated / "codex-home"
    source = home / "sessions"
    source.mkdir(parents=True, exist_ok=bool(args.resume_probe))
    workspace = allocated / "workspace"
    workspace.mkdir(exist_ok=bool(args.resume_probe))
    capture = allocated / "capture"
    receiver = ROOT / "src-tauri/resources/memory-capture/memory-capture.exe"
    status = dispatch(capture, {"method": "status"}, receiver)
    client = next(item for item in status["clients"] if item["provider"] == "codex")
    dispatch(capture, {"method": "configure", "provider": "codex", "source_root": str(source),
        "memory_roots": [], "enabled": True, "memory_enabled": False, "revision": client["revision"]}, receiver)
    dispatch(capture, {"method": "codex-hook", "action": "install", "codex_home": str(home)}, receiver)
    hook_path = home / "hooks.json"
    original_hooks = hook_path.read_bytes()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    template = home / "config.toml" if args.resume_probe else ROOT / ".tools/codex-hook-probe/client-ez0ci1rs/codex-home/config.toml"
    config = re.sub(r'http://127\.0\.0\.1:\d+/v1', f'http://127.0.0.1:{server.server_address[1]}/v1', template.read_text())
    if not args.resume_probe:
        config += f'\n[projects.{json.dumps(str(workspace))}]\ntrust_level = "trusted"\n'
    (home / "config.toml").write_text(config, encoding="utf-8")
    environment = {key: value for key, value in os.environ.items() if key not in
        {"OPENAI_API_KEY", "CODEX_API_KEY", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}}
    environment.update(CODEX_HOME=str(home), NO_PROXY="127.0.0.1,localhost", OTEL_SDK_DISABLED="true")
    try:
        before = hooks_list(environment, workspace)
        expected = "trusted" if args.resume_probe else "untrusted"
        if len(before) != 3 or any(hook["trustStatus"] != expected for hook in before):
            raise RuntimeError("Expected three newly installed untrusted hooks")
        print(json.dumps({"phase": "review-ready", "probe_root": str(allocated), "codex_home": str(home),
            "workspace": str(workspace), "hook_states": [hook["trustStatus"] for hook in before]}), flush=True)
        gate = allocated / "review-complete"
        deadline = time.monotonic() + 240
        while not args.resume_probe and not gate.exists():
            if time.monotonic() >= deadline:
                raise RuntimeError("Normal TUI review was not completed within the bounded wait")
            time.sleep(0.2)
        approved = hooks_list(environment, workspace)
        if len(approved) != 3 or any(hook["trustStatus"] != "trusted" or hook["isManaged"] for hook in approved):
            raise RuntimeError("Normal persisted user-hook trust was not observed")
        session_id = args.existing_session
        for turn in range(0 if args.existing_session else 2):
            command = [str(CODEX), "exec", "--skip-git-repo-check", "--json"]
            if session_id:
                command.extend(["resume", session_id])
            command.append("Synthetic trust check: SQLite stores the local vault. Return only the fixture reply.")
            result = subprocess.run(command, cwd=workspace, env=environment, capture_output=True, timeout=45)
            if result.returncode:
                raise RuntimeError("Fresh installed client without bypass failed")
            events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith(b"{")]
            started = next(item for item in events if item.get("type") == "thread.started")
            session_id = started["thread_id"]
            if not any(item.get("type") == "turn.completed" for item in events):
                raise RuntimeError("No completed turn without bypass")
            dispatch(capture, {"method": "index"}, receiver)
            plan = dispatch(capture, {"method": "import-plan", "offset": 0}, receiver)
            candidates = [item for item in plan["candidates"] if item["session_id"] == session_id]
            if len(candidates) != 1:
                raise RuntimeError("Trusted hook did not capture one canonical source")
            candidate = candidates[0]
            complete = next(source.rglob("*" + session_id + ".jsonl")).read_bytes()
            if candidate["source_text"].encode() != complete:
                raise RuntimeError("Trusted hook did not preserve exact source")
        if args.existing_session:
            dispatch(capture, {"method": "index"}, receiver)
            plan = dispatch(capture, {"method": "import-plan", "offset": 0}, receiver)
            candidates = [item for item in plan["candidates"] if item["session_id"] == session_id]
            if len(candidates) != 1:
                raise RuntimeError("Expected the already verified synthetic Session")
            candidate = candidates[0]
            complete = next(source.rglob("*" + session_id + ".jsonl")).read_bytes()
            if candidate["source_text"].encode() != complete:
                raise RuntimeError("Existing synthetic source differs")
        vault = Vault(allocated / "v2", create=True)
        vault_dispatch(vault, {"protocol_version": 1, "id": "trust-check", "method": "captures.ingest", "params": candidate})
        answer = vault.ask_sessions("SQLite local vault")
        if answer["status"] != "answered" or not any("SQLite" in item["quote"] for item in answer["sources"]):
            raise RuntimeError("Trusted source Ask failed")
        hooks = json.loads(original_hooks)
        hooks["hooks"]["Stop"][0]["hooks"][0]["timeout"] += 1
        hook_path.write_text(json.dumps(hooks), encoding="utf-8")
        changed = hooks_list(environment, workspace)
        modified = next(hook for hook in changed if hook["eventName"] == "stop")
        if modified["trustStatus"] != "modified":
            raise RuntimeError("Changed hook did not require fresh review")
        report = {"normal_persisted_trust_verified": True, "bypass_used": False,
            "session_id": session_id,
            "finished_existing_session": bool(args.existing_session),
            "managed_policy_used": False, "actual_tui_review": True, "fresh_client_turns": 2,
            "changed_definition_requires_review": True, "fixture_not_ai": True,
            "exact_rollout": True, "one_session": True, "source_bytes": len(complete), "ask_evidence": True,
            "probe_root": str(allocated)}
        (allocated / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report), flush=True)
    finally:
        hook_path.write_bytes(original_hooks)
        dispatch(capture, {"method": "codex-hook", "action": "remove", "codex_home": str(home)}, receiver)
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
