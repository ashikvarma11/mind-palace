"""Real Codex lifecycle verification with a loopback fixture, never real AI."""
from __future__ import annotations

import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]

TEXT = "Synthetic fixture: SQLite stores the local vault. This is test text, not model inference."


class Fixture(BaseHTTPRequestHandler):
    requests = 0
    live_seconds = 0
    hold_response = False
    request_started = threading.Event()
    release_response = threading.Event()

    def log_message(self, *_args: object) -> None:
        pass

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        if self.path != "/v1/responses" or self.headers.get("Authorization") or not 0 < length <= 4 * 1024 * 1024:
            self.send_error(400)
            return
        request = json.loads(self.rfile.read(length))
        if not isinstance(request, dict) or request.get("stream") is not True:
            self.send_error(400)
            return
        Fixture.requests += 1
        if Fixture.hold_response:
            Fixture.request_started.set()
            Fixture.release_response.wait(15)
            self.close_connection = True
            return
        item_id = "msg_" + uuid.uuid4().hex
        part = {"type": "output_text", "text": TEXT, "annotations": [], "logprobs": []}
        item = {"id": item_id, "type": "message", "status": "completed", "role": "assistant", "content": [part]}
        response = {"id": "resp_" + uuid.uuid4().hex, "object": "response", "created_at": int(time.time()),
                    "status": "in_progress", "output": [], "model": "gpt-6-sol", "error": None,
                    "usage": None, "incomplete_details": None}
        events = [
            {"type": "response.created", "response": dict(response)},
            {"type": "response.output_item.added", "output_index": 0,
             "item": {**item, "status": "in_progress", "content": []}},
            {"type": "response.content_part.added", "item_id": item_id, "output_index": 0,
             "content_index": 0, "part": {**part, "text": ""}},
            {"type": "response.output_text.delta", "item_id": item_id, "output_index": 0,
             "content_index": 0, "delta": TEXT},
            {"type": "response.output_text.done", "item_id": item_id, "output_index": 0,
             "content_index": 0, "text": TEXT},
            {"type": "response.content_part.done", "item_id": item_id, "output_index": 0,
             "content_index": 0, "part": part},
            {"type": "response.output_item.done", "output_index": 0, "item": item},
            {"type": "response.completed", "response": {**response, "status": "completed", "output": [item],
             "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2,
                       "input_tokens_details": {"cached_tokens": 0}, "output_tokens_details": {"reasoning_tokens": 0}}}},
        ]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Connection", "close")
        self.end_headers()
        for sequence, event in enumerate(events):
            # Keep one actual client process and its first turn alive for the
            # approved duration. Later resumed turns remain fast. This proves a
            # live streamed turn, not 20 turns in one interactive process.
            if sequence == len(events) - 1 and Fixture.requests == 1 and Fixture.live_seconds:
                time.sleep(Fixture.live_seconds)
            event["sequence_number"] = sequence
            self.wfile.write(("event: " + str(event["type"]) + "\ndata: " + json.dumps(event) + "\n\n").encode())
            self.wfile.flush()
        self.close_connection = True


def relay(marker: Path, command_token: str) -> int:
    raw = sys.stdin.buffer.read(65537)
    if len(raw) > 65536:
        return 2
    event = json.loads(raw)
    name = event.get("hook_event_name")
    if name not in {"SessionStart", "Stop", "SessionEnd"}:
        return 2
    command = base64.b64decode(command_token, validate=True).decode("utf-8")
    started = time.perf_counter()
    outcomes = marker.with_name("hook-outcomes.jsonl")
    def record(phase: str, code: str) -> None:
        with outcomes.open("a", encoding="ascii") as stream:
            stream.write(json.dumps({"event": name, "phase": phase, "code": code,
                "milliseconds": round((time.perf_counter() - started) * 1000)}) + "\n")
    record("started", "PENDING")
    # Respect the distinct installed budgets. A three-second end-event budget
    # must not be imposed on the ten-second startup/Stop handlers.
    try:
        result = subprocess.run(command, input=raw, capture_output=True,
                                timeout=2.8 if name == "SessionEnd" else 9.0)
    except subprocess.TimeoutExpired:
        record("finished", "TIMEOUT")
        return 1
    if result.returncode or result.stdout:
        record("finished", "RECEIVER_FAILED")
        return 1
    record("finished", "OK")
    with marker.open("a", encoding="ascii") as stream:
        stream.write(name + "\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-executable", type=Path, default=Path(os.environ.get("CODEX_CLI_PATH", "")))
    parser.add_argument("--turns", type=int, choices=range(1, 21), default=1)
    parser.add_argument("--require-session-end", action="store_true")
    parser.add_argument("--forced-exit", action="store_true")
    parser.add_argument("--live-seconds", type=int, choices=range(0, 121), default=0)
    parser.add_argument("--relay", action="store_true")
    parser.add_argument("--marker", type=Path)
    parser.add_argument("--command-b64")
    args = parser.parse_args()
    if args.relay:
        return relay(args.marker, args.command_b64)
    Fixture.live_seconds = args.live_seconds
    # Event recording must not load the vault/schema stack before the timed
    # frozen hook. Those imports belong only to this verification controller.
    sys.path.insert(0, str(ROOT / "sidecar"))
    from memory_worker.capture_control import dispatch
    from memory_worker.service import dispatch as vault_dispatch
    from memory_worker.vault import Vault
    if not args.codex_executable.is_absolute() or not args.codex_executable.is_file():
        parser.error("An absolute installed Codex executable is required")
    base = ROOT / ".tools/codex-hook-probe"
    base.mkdir(parents=True, exist_ok=True)
    allocated = Path(tempfile.mkdtemp(prefix="client-", dir=base))
    home = allocated / "codex-home"
    source = home / "sessions"
    source.mkdir(parents=True)
    workspace = allocated / "workspace"
    workspace.mkdir()
    capture_root = allocated / "capture"
    receiver = ROOT / "src-tauri/resources/memory-capture/memory-capture.exe"
    initial = dispatch(capture_root, {"method": "status"}, receiver)
    client = next(item for item in initial["clients"] if item["provider"] == "codex")
    dispatch(capture_root, {"method": "configure", "provider": "codex", "source_root": str(source),
                           "memory_roots": [], "enabled": True, "memory_enabled": False,
                           "revision": client["revision"]}, receiver)
    dispatch(capture_root, {"method": "codex-hook", "action": "install", "codex_home": str(home)}, receiver)
    marker = allocated / "events.txt"
    hook_path = home / "hooks.json"
    original_hooks = hook_path.read_bytes()
    hooks = json.loads(original_hooks)
    for groups in hooks["hooks"].values():
        for group in groups:
            for handler in group["hooks"]:
                token = base64.b64encode(handler["command"].encode()).decode("ascii")
                handler["command"] = subprocess.list2cmdline([sys.executable, str(Path(__file__).resolve()),
                    "--relay", "--marker", str(marker), "--command-b64", token])
    hook_path.write_text(json.dumps(hooks), encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    config = f'''model = "gpt-6-sol"
model_provider = "mind_palace_fixture"
web_search = "disabled"
project_root_markers = []
check_for_update_on_startup = false
[model_providers.mind_palace_fixture]
name = "Local verification fixture (not AI)"
base_url = "http://127.0.0.1:{port}/v1"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
request_max_retries = 0
stream_max_retries = 0
[analytics]
enabled = false
[feedback]
enabled = false
[otel]
exporter = "none"
trace_exporter = "none"
metrics_exporter = "none"
log_user_prompt = false
[memories]
generate_memories = false
use_memories = false
[skills.bundled]
enabled = false
[apps._default]
enabled = false
'''
    (home / "config.toml").write_text(config, encoding="utf-8")
    environment = {key: value for key, value in os.environ.items() if key not in
                   {"OPENAI_API_KEY", "CODEX_API_KEY", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}}
    environment.update(CODEX_HOME=str(home), NO_PROXY="127.0.0.1,localhost", OTEL_SDK_DISABLED="true")
    session_id = None
    first_client_seconds = 0.0
    turn_observations = []
    try:
        for turn in range(args.turns):
            before_events = marker.read_text().splitlines() if marker.exists() else []
            command = [str(args.codex_executable), "exec", "--dangerously-bypass-hook-trust", "--skip-git-repo-check", "--json"]
            if session_id:
                command.extend(["resume", session_id])
            command.append(f"Synthetic turn {turn + 1}: SQLite is the local vault database. Return the test response only.")
            client_started = time.monotonic()
            result = subprocess.run(command, cwd=workspace, env=environment, capture_output=True,
                                    timeout=35 + (args.live_seconds if turn == 0 else 0))
            if turn == 0:
                first_client_seconds = time.monotonic() - client_started
                if first_client_seconds < args.live_seconds:
                    raise RuntimeError("Client did not remain alive for the required duration")
                print(json.dumps({"phase": "live-turn-complete", "seconds": round(first_client_seconds, 3)}), flush=True)
            if result.returncode:
                # Only this isolated synthetic run can appear here. Keep output in the ignored probe.
                (allocated / "client-error.txt").write_bytes(result.stderr[-16384:])
                raise RuntimeError("Installed Codex fixture run failed; see isolated client-error.txt")
            events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith(b"{")]
            started = next((item for item in events if item.get("type") == "thread.started"), None)
            if started:
                session_id = started["thread_id"]
            if not session_id or not any(item.get("type") == "turn.completed" for item in events):
                raise RuntimeError("Codex did not report a completed synthetic turn")
            after_events = marker.read_text().splitlines() if marker.exists() else []
            turn_observations.append({"turn": turn + 1, "client_completed": True,
                "verified_hooks": after_events[len(before_events):],
                "hook_warning_in_stderr": b"hook" in result.stderr.lower()})
            print(json.dumps({"phase": "turn-hooks", **turn_observations[-1]}), flush=True)
        rollout = next(source.rglob("*.jsonl"))
        if args.forced_exit:
            Fixture.hold_response = True
            forced_prompt = "Synthetic forced-exit prompt: preserve this local test record."
            command = [str(args.codex_executable), "exec", "--dangerously-bypass-hook-trust", "--skip-git-repo-check", "--json",
                       "resume", session_id, forced_prompt]
            child = subprocess.Popen(command, cwd=workspace, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                if not Fixture.request_started.wait(10):
                    raise RuntimeError("Forced-exit fixture request did not start")
                deadline = time.monotonic() + 10
                while forced_prompt.encode() not in rollout.read_bytes():
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Forced-exit prompt was not persisted")
                    time.sleep(0.05)
                # Kill only the isolated installed client owned by this test,
                # while its fixture response is held and before Stop can run.
                child.kill()
                child.communicate(timeout=5)
            finally:
                if child.poll() is None:
                    child.kill()
                    child.communicate(timeout=5)
                Fixture.release_response.set()
        delivered = marker.read_text().splitlines() if marker.exists() else []
        if "Stop" not in delivered:
            raise RuntimeError("Actual Stop delivery was not observed")
        dispatch(capture_root, {"method": "index"}, receiver)
        plan = dispatch(capture_root, {"method": "import-plan", "offset": 0}, receiver)
        if len(plan["candidates"]) != 1:
            raise RuntimeError("Expected one captured provider Session")
        candidate = plan["candidates"][0]
        complete = rollout.read_bytes()
        if candidate["source_text"].encode() != complete:
            raise RuntimeError("Captured source differs from the complete isolated Codex rollout")
        vault = Vault(allocated / "vault", create=True)
        vault_dispatch(vault, {"protocol_version": 1, "id": "client-check", "method": "captures.ingest", "params": candidate})
        answer = vault.ask_sessions("Which database stores the local vault?")
        if answer["status"] != "answered" or not any("SQLite" in entry["quote"] for entry in answer["sources"]):
            raise RuntimeError("Stored-session evidence answer failed")
        report = {"installed_codex": True, "fixture_not_ai": True, "turns": args.turns,
                  "live_seconds_requested": args.live_seconds,
                  "first_client_seconds": round(first_client_seconds, 3),
                  "single_live_turn_then_resumed_turns": True,
                  "turn_observations": turn_observations,
                  "all_completed_turn_hooks_verified": delivered.count("Stop") == args.turns and
                      delivered.count("SessionEnd") == args.turns,
                  "requests": Fixture.requests, "hook_events": delivered, "one_session": True,
                  "stop_events": delivered.count("Stop"), "start_events": delivered.count("SessionStart"),
                  "end_events": delivered.count("SessionEnd"), "forced_exit": args.forced_exit,
                  "session_end_observed": "SessionEnd" in delivered,
                  "exact_rollout": True, "source_bytes": len(complete), "ask_evidence": True}
        (allocated / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({**report, "probe_root": str(allocated)}))
        if delivered.count("Stop") != args.turns:
            raise RuntimeError("Not every completed turn delivered a verified Stop hook")
        if args.require_session_end and delivered.count("SessionEnd") != args.turns:
            raise RuntimeError("Not every normal exit delivered a verified SessionEnd hook")
    finally:
        hook_path.write_bytes(original_hooks)
        dispatch(capture_root, {"method": "codex-hook", "action": "remove", "codex_home": str(home)}, receiver)
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
