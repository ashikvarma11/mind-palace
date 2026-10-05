"""App-owned consent/control. Never edits assistant settings or enumerates source contents."""
from __future__ import annotations

import base64
import datetime
from pathlib import Path
import re
import tomllib
import uuid
from typing import TypedDict

import portalocker

from .atomic_io import file_hash, write
from .capture_inbox import inspect_snapshot, memory_consent, read_health, read_session_snapshot, rebuild_index, snapshot_memory
from .chatgpt_sync import encoded, sha
from .session_capture import MAX_EVENT, PROVIDERS, dedicated, fail, strict_json
from .paths import no_links

IMPORT_PAGE = 10
IMPORT_TEXT_BYTES = 20 * 1024 * 1024
IMPORT_PAGE_BYTES = 48 * 1024 * 1024
IMPORT_NAMESPACE = uuid.UUID("51df59b9-0d04-4fb1-b7a0-554e8915ca6e")
HEX = re.compile(r"[0-9a-f]{64}", re.ASCII)


class ClientStatus(TypedDict):
    provider: str
    configured: bool
    enabled: bool
    memory_enabled: bool
    source_root: str
    memory_roots: list[str]
    revision: str
    snippet: str


def display(path: Path) -> str:
    value = str(path)
    if value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    return value[4:] if value.startswith("\\\\?\\") else value


def paths(root: Path, provider: str) -> tuple[Path, Path]:
    return root / "settings" / (provider + ".json"), root / "settings" / (provider + "-memory.json")


def read(path: Path) -> bytes | None:
    no_links(path)
    if not path.exists():
        return None
    with path.open("rb") as stream:
        raw = stream.read(MAX_EVENT + 1)
    if len(raw) > MAX_EVENT:
        fail("LIMIT_EXCEEDED")
    return raw


def revision(session: bytes | None, memory: bytes | None) -> str:
    return sha(encoded([None if session is None else sha(session), None if memory is None else sha(memory)]))


def snippets(provider: str, executable: Path, session: Path, memory: Path) -> str:
    args = ["--config", display(session)]
    if provider == "claude-code":
        handler: dict[str, object] = {"type": "command", "command": str(executable), "args": args}
    elif all(re.fullmatch(r"[A-Za-z0-9_./:\\-]+", value, re.ASCII) for value in [str(executable), *args]):
        # Codex already starts its configured shell. Safe single tokens need
        # no additional interpreter, which avoids its cold-start cost inside
        # the three-second SessionEnd budget. Other paths keep literal quoting.
        handler = {"type": "command", "command": " ".join([str(executable), *args])}
    else:
        # Shell-independent outer command: only ASCII base64. Literal PS strings
        # prevent filenames from becoming commands, interpolation or substitutions.
        quote = lambda value: "'" + value.replace("'", "''") + "'"
        script = "& " + quote(str(executable)) + " " + " ".join(quote(arg) for arg in args) + "; exit $LASTEXITCODE"
        token = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        handler = {"type": "command", "command": "powershell.exe -NoProfile -NonInteractive -EncodedCommand " + token}
    hooks = {event: [{"hooks": [{**handler, "timeout": 3 if event == "SessionEnd" else 10}]}]
             for event in ("SessionStart", "Stop", "SessionEnd")}
    import json
    return json.dumps({"hooks": hooks}, indent=2)


def codex_hook(root: Path, executable: Path, request: dict[str, object]) -> dict[str, object]:
    """Merge or remove only this receiver's exact user-level handlers."""
    if set(request) != {"method", "action", "codex_home"} or request.get("action") not in ("status", "install", "remove"):
        fail("VALIDATION_ERROR")
    codex_home = dedicated(request["codex_home"])
    target = codex_home / "hooks.json"
    no_links(target)
    if not codex_home.is_dir():
        fail("UNAVAILABLE")
    configured = client(root, "codex", executable)
    if not configured["configured"]:
        fail("UNAVAILABLE")
    session, memory = paths(root, "codex")
    expected = strict_json(snippets("codex", executable, session, memory).encode("utf-8"))["hooks"]
    original = read(target)
    value = {"hooks": {}} if original is None else strict_json(original)
    if not isinstance(value, dict) or ("hooks" in value and not isinstance(value["hooks"], dict)):
        fail("VALIDATION_ERROR")
    hooks = value.setdefault("hooks", {})
    counts = []
    for event, groups in expected.items():
        current = hooks.get(event, [])
        if not isinstance(current, list):
            fail("VALIDATION_ERROR")
        ours = expected[event][0]["hooks"][0]
        count = 0
        for group in current:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                fail("VALIDATION_ERROR")
            for handler in group["hooks"]:
                if not isinstance(handler, dict):
                    fail("VALIDATION_ERROR")
                if handler == ours:
                    count += 1
        counts.append(count)
    if any(count > 1 for count in counts):
        fail("CONFLICT")
    state = "installed" if counts == [1, 1, 1] else "absent" if counts == [0, 0, 0] else "partial"
    if request["action"] == "status":
        return {"status": state, "config_path": display(target), "trust_verified": False}
    if state == "partial":
        fail("CONFLICT")
    if request["action"] == "install" and state == "installed":
        return {"status": "installed", "config_path": display(target), "trust_verified": False}
    if request["action"] == "remove" and state == "absent":
        return {"status": "absent", "config_path": display(target), "trust_verified": False}
    config = codex_home / "config.toml"
    no_links(config)
    if request["action"] == "install" and config.is_file():
        with config.open("rb") as stream:
            raw_config = stream.read(1024 * 1024 + 1)
        if len(raw_config) > 1024 * 1024:
            fail("LIMIT_EXCEEDED")
        try:
            inline = tomllib.loads(raw_config.decode("utf-8"))
        except (ValueError, UnicodeError):
            fail("VALIDATION_ERROR")
        if "hooks" in inline:
            inline_hooks = inline["hooks"]
            # Codex's normal /hooks review persists approvals under hooks.state.
            # These records are not inline handler definitions. Keep their bytes
            # intact while still refusing mixed or ambiguous inline hook config.
            if not isinstance(inline_hooks, dict) or set(inline_hooks) != {"state"} or not isinstance(inline_hooks["state"], dict):
                fail("CONFLICT")
    import copy
    changed = copy.deepcopy(value)
    for event in expected:
        groups = changed["hooks"].get(event, [])
        ours = expected[event][0]["hooks"][0]
        if request["action"] == "install":
            groups.append(expected[event][0])
        else:
            groups = [{**group, "hooks": [item for item in group["hooks"] if item != ours]}
                      for group in groups]
            groups = [group for group in groups if group["hooks"]]
        changed["hooks"][event] = groups
    backup = root / "settings" / "codex-hooks-backups" / (str(uuid.uuid4()) + ".json")
    no_links(backup)
    write(backup, original if original is not None else b"", None)
    write(target, encoded(changed), file_hash(target))
    return {"status": "installed" if request["action"] == "install" else "absent",
            "config_path": display(target), "trust_verified": False}


def client(root: Path, provider: str, executable: Path) -> ClientStatus:
    session, memory = paths(root, provider)
    first, second = read(session), read(memory)
    result: ClientStatus = {"provider": provider, "configured": False, "enabled": False,
                            "memory_enabled": False, "source_root": "", "memory_roots": [],
                            "revision": revision(first, second), "snippet": ""}
    if first is None and second is None:
        return result
    if first is None or second is None:
        fail("CONFLICT")
    # Validate even disabled consent, but don't read any source content.
    config = strict_json(first)
    if not isinstance(config, dict) or set(config) != {"schema_version", "provider", "enabled", "source_root", "inbox_root"} or type(config["schema_version"]) is not int or config["schema_version"] != 1 or type(config["enabled"]) is not bool:
        fail("VALIDATION_ERROR")
    source, inbox = dedicated(config["source_root"]), dedicated(config["inbox_root"])
    consent = memory_consent(memory)
    if config["provider"] != provider or consent.provider != provider or inbox != root / "inbox" or consent.inbox != inbox:
        fail("CONFLICT")
    if any(folder == root or folder in root.parents or root in folder.parents for folder in [source, *consent.roots]):
        fail("VALIDATION_ERROR")
    result.update(configured=True, enabled=config["enabled"], memory_enabled=consent.enabled,
                  source_root=display(source), memory_roots=[display(item) for item in consent.roots],
                  snippet=snippets(provider, executable, session, memory))
    return result


def status(root: Path, executable: Path) -> dict[str, object]:
    return {"schema_version": 1, "inbox_root": display(root / "inbox"),
            "health": read_health(root / "inbox"),
            "clients": [client(root, provider, executable) for provider in sorted(PROVIDERS)]}


def configure(root: Path, request: dict[str, object], executable: Path) -> dict[str, object]:
    fields = {"method", "provider", "source_root", "memory_roots", "enabled", "memory_enabled", "revision"}
    if set(request) != fields or not isinstance(request["provider"], str) or request["provider"] not in PROVIDERS:
        fail("VALIDATION_ERROR")
    provider = str(request["provider"])
    if type(request["enabled"]) is not bool or type(request["memory_enabled"]) is not bool:
        fail("VALIDATION_ERROR")
    roots = request["memory_roots"]
    if not isinstance(roots, list) or len(roots) > 32 or (request["memory_enabled"] and not roots):
        fail("VALIDATION_ERROR")
    source = dedicated(request["source_root"])
    selected = [dedicated(value) for value in roots]
    inbox = root / "inbox"
    if request["enabled"] and not source.is_dir():
        fail("VALIDATION_ERROR")
    for folder in [source, *selected]:
        if folder == root or folder in root.parents or root in folder.parents:
            fail("VALIDATION_ERROR")
    for folder in selected:
        if folder.exists() and not folder.is_dir():
            fail("VALIDATION_ERROR")
        if any(other != folder and (other in folder.parents or folder in other.parents) for other in selected):
            fail("VALIDATION_ERROR")
    if len(set(selected)) != len(selected):
        fail("VALIDATION_ERROR")
    no_links(root / "settings")
    (root / "settings").mkdir(parents=True, exist_ok=True)
    no_links(inbox)
    inbox.mkdir(parents=True, exist_ok=True)
    no_links(inbox / "capture.lock")
    with portalocker.Lock(str(inbox / "capture.lock"), mode="a", timeout=1, check_interval=0.05):
        session, memory = paths(root, provider)
        first, second = read(session), read(memory)
        if request["revision"] != revision(first, second):
            fail("CONFLICT")
        # Refuse externally redirected/malformed files, rather than replacing them.
        client(root, provider, executable)
        transcript = {"schema_version": 1, "provider": provider, "enabled": False,
                      "source_root": display(source), "inbox_root": display(inbox)}
        # Publish paused first. An interrupted scope update stays paused until
        # explicit refresh/retry; hooks also recheck this consent under this lock.
        write(session, encoded(transcript), file_hash(session))
        mem = {"schema_version": 1, "provider": provider, "enabled": request["memory_enabled"],
               "inbox_root": display(inbox), "roots": [display(item) for item in selected]}
        write(memory, encoded(mem), file_hash(memory))
        transcript["enabled"] = request["enabled"]
        write(session, encoded(transcript), file_hash(session))
        return status(root, executable)


def import_plan(root: Path, executable: Path, offset: int) -> dict[str, object]:
    """Return validated bounded data, never a caller-selected file path."""
    configured = [provider for provider in sorted(PROVIDERS) if client(root, provider, executable)["configured"]]
    if not configured:
        fail("UNAVAILABLE")
    rebuild_index(paths(root, configured[0])[0], allow_paused=True)
    index_path = root / "inbox" / "index.json"
    no_links(index_path)
    if not index_path.is_file():
        fail("UNAVAILABLE")
    with index_path.open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        fail("LIMIT_EXCEEDED")
    value = strict_json(raw)
    if not isinstance(value, dict) or set(value) != {"schema_version", "kind", "derived", "entries"} or value.get("schema_version") != 1 or value.get("kind") != "capture_index" or value.get("derived") is not True or not isinstance(value.get("entries"), list):
        fail("VALIDATION_ERROR")
    groups: dict[tuple[str, str], list[dict[str, object]]] = {}
    oversized: set[tuple[str, str]] = set()
    memories: set[tuple[str, str]] = set()
    inbox = root / "inbox"
    for entry in value["entries"]:
        if not isinstance(entry, dict) or set(entry) != {"provider", "kind", "key", "sha256", "path", "bytes"}:
            fail("VALIDATION_ERROR")
        provider, kind, key, relative = entry.get("provider"), entry.get("kind"), entry.get("key"), entry.get("path")
        if not isinstance(provider, str) or provider not in PROVIDERS or kind not in ("session", "memory") or not isinstance(key, str) or not isinstance(relative, str):
            fail("VALIDATION_ERROR")
        target = inbox / Path(relative)
        checked = inspect_snapshot(target, provider, kind, key)
        if checked["sha256"] != entry.get("sha256") or checked["bytes"] != entry.get("bytes"):
            fail("CONFLICT")
        if kind == "memory":
            memories.add((provider, key))
            continue
        if checked["bytes"] > IMPORT_TEXT_BYTES:
            groups.setdefault((provider, key), [])
            oversized.add((provider, key))
            continue
        groups.setdefault((provider, key), []).append({**checked, "path": relative})
    page: list[dict[str, object]] = []
    skipped = valid_count = page_bytes = 0
    next_offset = None
    for (provider, key), snapshots in sorted(groups.items()):
        if (provider, key) in oversized or not snapshots:
            skipped += 1
            continue
        ordered = sorted(snapshots, key=lambda item: (int(item["bytes"]), str(item["sha256"])))
        previous = b""
        session_id = None
        divergent = False
        for item in ordered:
            metadata, current = read_session_snapshot(inbox / str(item["path"]), provider, key)
            if session_id is not None and metadata["session_id"] != session_id:
                fail("CONFLICT")
            session_id = str(metadata["session_id"])
            if not current.startswith(previous):
                divergent = True
                break
            previous = current
        if divergent:
            skipped += 1
            continue
        valid_count += 1
        if valid_count <= offset:
            continue
        selected = ordered[-1]
        text = previous.decode("utf-8")
        revisions = [str(item["sha256"]) for item in ordered]
        label = "Codex" if provider == "codex" else "Claude Code"
        fingerprint = provider + "\0" + key + "\0" + sha(encoded(revisions))
        candidate = {"op_id": str(uuid.uuid5(IMPORT_NAMESPACE, fingerprint)), "provider": provider,
                         "session_key": key, "session_id": session_id,
                         "title": (label + " session " + session_id)[:200], "source_text": text,
                         "selected_sha256": str(selected["sha256"]), "revisions": revisions}
        candidate_bytes = len(encoded(candidate))
        if candidate_bytes > IMPORT_PAGE_BYTES:
            fail("LIMIT_EXCEEDED")
        if len(page) >= IMPORT_PAGE or page_bytes + candidate_bytes > IMPORT_PAGE_BYTES:
            next_offset = offset + len(page)
            break
        page.append(candidate)
        page_bytes += candidate_bytes
    return {"schema_version": 1, "candidates": page, "skipped": skipped,
            "memories_pending": len(memories), "next_offset": next_offset}


def acknowledge(root: Path, request: dict[str, object]) -> dict[str, object]:
    fields = {"method", "provider", "session_key", "selected_sha256", "canonical_session_id"}
    if set(request) != fields:
        fail("VALIDATION_ERROR")
    provider = request.get("provider")
    key = request.get("session_key")
    selected = request.get("selected_sha256")
    canonical = request.get("canonical_session_id")
    if (not isinstance(provider, str) or provider not in PROVIDERS or not isinstance(key, str)
            or not HEX.fullmatch(key) or not isinstance(selected, str) or not HEX.fullmatch(selected)
            or not isinstance(canonical, str)):
        fail("VALIDATION_ERROR")
    try:
        if str(uuid.UUID(canonical)) != canonical:
            fail("VALIDATION_ERROR")
    except ValueError:
        fail("VALIDATION_ERROR")
    snapshot = root / "inbox" / provider / key / (selected + ".json")
    metadata, selected_bytes = read_session_snapshot(snapshot, provider, key)
    if sha(selected_bytes) != selected:
        fail("CONFLICT")
    target = root / "inbox" / "imported" / provider / (key + ".json")
    no_links(target)
    previous = file_hash(target)
    if previous is not None:
        existing = strict_json(target.read_bytes())
        expected = {"schema_version", "kind", "provider", "session_key", "session_id",
                    "selected_sha256", "canonical_session_id", "acknowledged_at"}
        if (not isinstance(existing, dict) or set(existing) != expected
                or any(existing.get(name) != value for name, value in
                       (("schema_version", 1), ("kind", "vault_import"), ("provider", provider),
                        ("session_key", key), ("session_id", metadata["session_id"]),
                        ("canonical_session_id", canonical)))):
            fail("CONFLICT")
        old = existing.get("selected_sha256")
        if not isinstance(old, str) or not HEX.fullmatch(old):
            fail("VALIDATION_ERROR")
        if old == selected:
            return {"status": "unchanged"}
        _, old_bytes = read_session_snapshot(root / "inbox" / provider / key / (old + ".json"), provider, key)
        if not selected_bytes.startswith(old_bytes):
            fail("CONFLICT")
    value = {"schema_version": 1, "kind": "vault_import", "provider": provider,
             "session_key": key, "session_id": metadata["session_id"],
             "selected_sha256": selected, "canonical_session_id": canonical,
             "acknowledged_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write(target, encoded(value), previous)
    return {"status": "acknowledged"}


def dispatch(root_path: str | Path, request: object, executable: Path) -> dict[str, object]:
    root = dedicated(str(root_path))
    if not isinstance(request, dict) or not isinstance(request.get("method"), str):
        fail("VALIDATION_ERROR")
    if request["method"] == "configure":
        return configure(root, request, executable)
    if request["method"] == "import-plan":
        if set(request) != {"method", "offset"} or type(request["offset"]) is not int or not 0 <= request["offset"] <= 5000:
            fail("VALIDATION_ERROR")
        return import_plan(root, executable, request["offset"])
    if request["method"] == "acknowledge":
        return acknowledge(root, request)
    if request["method"] == "codex-hook":
        return codex_hook(root, executable, request)
    if request["method"] in {"recover", "history-preview", "history-import"}:
        from .capture_recovery import history_import, history_preview, recover_known
        session_path, _ = paths(root, "codex")
        if request["method"] in {"recover", "history-preview"}:
            if set(request) != {"method"}:
                fail("VALIDATION_ERROR")
            if request["method"] == "recover":
                rebuild_index(session_path, allow_paused=True)
                result = recover_known(session_path)
                if result["restored"]:
                    rebuild_index(session_path, allow_paused=True)
                return result
            with portalocker.Lock(str(root / "inbox/capture.lock"), mode="a", timeout=1, check_interval=0.05):
                return history_preview(root, session_path)
        if (set(request) != {"method", "preview_id", "offset"} or not isinstance(request["preview_id"], str)
                or type(request["offset"]) is not int or not 0 <= request["offset"] <= 1000):
            fail("VALIDATION_ERROR")
        try:
            if str(uuid.UUID(request["preview_id"])) != request["preview_id"]:
                fail("VALIDATION_ERROR")
        except ValueError:
            fail("VALIDATION_ERROR")
        with portalocker.Lock(str(root / "inbox/capture.lock"), mode="a", timeout=1, check_interval=0.05):
            return history_import(root, session_path, request["preview_id"], request["offset"])
    if set(request) != {"method"}:
        fail("VALIDATION_ERROR")
    if request["method"] == "status":
        return status(root, executable)
    if request["method"] == "cleanup":
        from .capture_inbox import prune_redundant
        configured = [provider for provider in sorted(PROVIDERS) if client(root, provider, executable)["configured"]]
        if not configured:
            fail("UNAVAILABLE")
        config_path = paths(root, configured[0])[0]
        result = prune_redundant(config_path)
        if result["removed_revisions"]:
            rebuild_index(config_path, allow_paused=True)
        return result
    if request["method"] == "index":
        first: Path | None = None
        for provider in sorted(PROVIDERS):
            if client(root, provider, executable)["configured"]:
                session_path, memory_path = paths(root, provider)
                if first is None:
                    first = session_path
                snapshot_memory(session_path, memory_path)
        if first is not None:
            result = rebuild_index(first, allow_paused=True)
            if client(root, "codex", executable)["configured"]:
                from .capture_recovery import recover_known
                recovered = recover_known(paths(root, "codex")[0])
                if recovered["restored"]:
                    result = rebuild_index(first, allow_paused=True)
            if result["status"] == "empty":
                result["status"] = "indexed"
            return result
        fail("UNAVAILABLE")
    fail("VALIDATION_ERROR")
    return {}  # Unreachable; keeps the external return contract explicit.
