import datetime
import json
import os
import re
import uuid
from contextlib import contextmanager
import portalocker
from .atomic_io import digest, file_hash, write
from .contracts import validate, object_params
from .errors import WorkerError
from .journal import Journal, encoded, load
from .paths import ID, no_links, owned_path, root_path


QUESTION_STOP_WORDS = frozenset({
    "about", "after", "again", "also", "been", "could", "does", "from", "have", "into",
    "just", "should", "that", "their", "there", "these", "they", "this", "what", "when",
    "where", "which", "with", "would", "your", "were", "will", "why", "did", "how", "the",
    "and", "for", "was", "are", "our", "you", "who", "can", "tell", "please",
    "choose", "chose", "chosen", "selected", "select", "decide", "decided", "choice", "stores", "store", "used", "use",
})


def identifier():
    return str(uuid.uuid4())


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


class Vault:
    def __init__(self, value, create=False):
        self.root = root_path(value)
        if create:
            if self.root.exists() and any(self.root.iterdir()):
                raise WorkerError("CONFLICT", "New vault directory must be empty.")
            self.root.mkdir(parents=True, exist_ok=True)
            manifest = {"schema_version": 1, "id": identifier(), "kind": "vault", "format": "mind-palace-foundation-v1"}
            write(self.root / ".memory/vault.json", encoded(manifest), None)
        self.manifest = load(self.root / ".memory/vault.json")
        validate("vault", self.manifest)
        from .cloud_preview import Previews
        self.previews = Previews()
        self.lock_path = self.root / ".memory/locks/write.lock"
        no_links(self.lock_path)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock():
            self.journal = Journal(self.root)
            self.journal.recover()

    @contextmanager
    def lock(self):
        no_links(self.lock_path)
        try:
            with portalocker.Lock(str(self.lock_path), mode="a", timeout=2):
                yield
        except portalocker.exceptions.LockException:
            raise WorkerError("BUSY", "Vault is in use; retry later.", True) from None

    def read_decision(self, record_id):
        value = load(owned_path(self.root, "records/" + record_id + ".json"))
        validate("memory-record", value)
        if value["id"] != record_id:
            raise WorkerError("VALIDATION_ERROR", "Record identity mismatch.")
        return value

    def session_header(self, record_id):
        """Read only bounded frontmatter; list operations never load source content."""
        path = owned_path(self.root, "sessions/" + record_id + ".md")
        if not path.is_file():
            raise WorkerError("NOT_FOUND", "Session is unavailable.")
        if path.stat().st_size > 1024 * 1024:
            raise WorkerError("VALIDATION_ERROR", "Stored file exceeds the supported bounds.")
        try:
            with path.open("rb") as stream:
                opening = stream.readline(8)
                front = stream.readline(8192)
                closing = stream.readline(8)
            if opening not in (b"---\n", b"---\r\n") or closing not in (b"---\n", b"---\r\n") or not front.endswith(b"\n"):
                raise ValueError()
            from .protocol import parse
            metadata = parse(front)
            validate("native-memory", metadata, "SessionMetadata")
            if metadata["id"] != record_id:
                raise ValueError()
            return metadata
        except (ValueError, KeyError, TypeError, UnicodeError):
            raise WorkerError("VALIDATION_ERROR", "Invalid session format.") from None

    def list_sessions(self, limit, offset):
        directory = self.root / "sessions"
        no_links(directory)
        if not directory.exists():
            return {"items": [], "total": 0, "next_offset": None}
        if not directory.is_dir():
            raise WorkerError("VALIDATION_ERROR", "Invalid sessions directory.")
        records = []
        with os.scandir(directory) as entries:
            for entry in entries:
                if len(records) >= 1000:
                    raise WorkerError("LIMIT_EXCEEDED", "Session listing supports up to 1000 records; existing files were preserved.")
                if not re.fullmatch(ID + r"\.md", entry.name):
                    raise WorkerError("VALIDATION_ERROR", "Unexpected session entry; existing files were preserved.")
                records.append(self.session_header(entry.name[:-3]))
        # Parse calendar instants: lexical fractions would misorder equal seconds.
        records.sort(key=lambda item: (datetime.datetime.fromisoformat(item["created_at"]), item["id"]), reverse=True)
        end = min(offset + limit, len(records))
        result = {"items": records[offset:end], "total": len(records),
                  "next_offset": end if end < len(records) else None}
        validate("native-memory", result, "SessionList")
        return result

    def read_session(self, record_id):
        metadata = self.session_header(record_id)
        path = owned_path(self.root, "sessions/" + record_id + ".md")
        file_hash(path)
        text = path.read_text(encoding="utf-8")
        try:
            start, front, body = text.split("\n", 2)
            metadata = json.loads(front)
            base_fields = {"schema_version", "id", "kind", "title", "source_id", "review_status", "created_at"}
            if start != "---" or not body.startswith("---\n") or set(metadata) not in (base_fields, base_fields | {"source_kind", "provider"}):
                raise ValueError()
            if metadata["schema_version"] != 1 or metadata["id"] != record_id or metadata["kind"] != "session" or metadata["review_status"] != "unreviewed":
                raise ValueError()
            validate("native-memory", metadata, "SessionMetadata")
            source_meta = load(owned_path(self.root, "sources/" + metadata["source_id"] + "/source.json"))
            from .service import HEX, UUID
            if source_meta.get("import_kind") == "pasted_text":
                source = owned_path(self.root, "sources/" + metadata["source_id"] + "/original.txt")
                valid = object_params({"schema_version": {"const": 1}, "id": UUID, "sha256": HEX,
                                       "bytes": {"type": "integer", "minimum": 0, "maximum": 262144}, "import_kind": {"const": "pasted_text"}}).is_valid(source_meta)
            else:
                valid = object_params({"schema_version": {"const": 1}, "id": UUID, "sha256": HEX,
                                       "bytes": {"type": "integer", "minimum": 0, "maximum": 20971520}, "import_kind": {"const": "hook_capture"},
                                       "provider": {"enum": ["claude-code", "codex"]}, "session_key": HEX,
                                       "session_id": {"type": "string", "pattern": "^[A-Za-z0-9_-]{1,128}$"},
                                       "selected_sha256": HEX,
                                       "revisions": {"type": "array", "minItems": 1, "maxItems": 5000, "uniqueItems": True, "items": HEX}}).is_valid(source_meta)
                if metadata.get("source_kind") != "hook_capture" or metadata.get("provider") != source_meta.get("provider"):
                    raise ValueError()
                source = owned_path(self.root, "sources/" + metadata["source_id"] + "/revisions/" + str(source_meta.get("selected_sha256")) + ".txt")
            if not valid or source_meta["id"] != metadata["source_id"]:
                raise ValueError()
            if file_hash(source) != source_meta["sha256"] or source.stat().st_size != source_meta["bytes"]:
                raise WorkerError("CONFLICT", "Original source changed; it was not overwritten.")
            result = {"metadata": metadata, "body": body[4:], "source_text": source.read_bytes().decode("utf-8")}
            validate("native-memory", result, "SessionRead")
            return result
        except (ValueError, KeyError, TypeError):
            raise WorkerError("VALIDATION_ERROR", "Invalid session format.") from None

    def ask_sessions(self, question):
        """Return bounded, exact excerpts from verified local session sources."""
        terms = []
        for term in re.findall(r"[^\W_]+", question.casefold(), re.UNICODE):
            if len(term) >= 3 and term not in QUESTION_STOP_WORDS and term not in terms:
                terms.append(term)
        if not terms:
            return {"schema_version": 1, "status": "insufficient_evidence",
                    "answer": "I could not identify a specific search term in that question.", "sources": []}
        candidates = []
        inventory = []
        offset = 0
        while offset < 1000:
            page = self.list_sessions(50, offset)
            inventory.extend(page["items"])
            if page["next_offset"] is None:
                break
            offset = page["next_offset"]
        for metadata in inventory:
            record = self.read_session(metadata["id"])
            text = record["source_text"]
            from .session_text import conversation_passages
            snapshot_hash = digest(text.encode("utf-8"))
            best = None
            for passage in conversation_passages(text, metadata.get("provider")):
                positions = [match for term in terms if (match := re.search(r"\b" + re.escape(term) + r"\b", passage.text, re.IGNORECASE))]
                if len(positions) != len(terms):
                    continue
                first = min(match.start() for match in positions)
                excerpt = passage.text[max(0, first - 240):first + 720]
                raw = text[passage.start:passage.end]
                raw_matches = [match for term in terms if (match := re.search(r"\b" + re.escape(term) + r"\b", raw, re.IGNORECASE))]
                raw_first = min((match.start() for match in raw_matches), default=0)
                start = passage.start + max(0, raw_first - 240)
                end = min(passage.end, start + 1200)
                quote = text[start:end]
                source = {"session_id": metadata["id"], "title": metadata["title"], "quote": quote,
                          "start": start, "end": end, "snapshot_sha256": snapshot_hash}
                if metadata.get("provider") is not None:
                    source["provider"] = metadata["provider"]
                score = (len(positions), -len(passage.text))
                if best is None or score > best[0]:
                    best = (score, source, excerpt)
            if best is not None:
                candidates.append((*best[0], metadata["created_at"], best[1], best[2]))
        if not candidates:
            return {"schema_version": 1, "status": "insufficient_evidence",
                    "answer": "I did not find matching evidence in the stored conversations.", "sources": []}
        candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        sources = [item[3] for item in candidates[:3]]
        answer = "The closest stored conversation passage is from " + sources[0]["title"] + ":\n\n" + candidates[0][4]
        result = {"schema_version": 1, "status": "answered", "answer": answer, "sources": sources}
        validate("native-memory", result, "MemoryAnswer")
        return result

    def call(self, method, params, after_write=None):
        with self.lock():
            self.journal.recover()
            if method == "sessions.read":
                return self.read_session(params["id"])
            if method == "sessions.list":
                return self.list_sessions(params["limit"], params["offset"])
            if method == "sessions.ask":
                return self.ask_sessions(params["question"])
            if method == "decisions.read":
                return self.read_decision(params["id"])
            if method not in ("sessions.create", "captures.ingest", "decisions.create", "decisions.confirm"):
                raise WorkerError("VALIDATION_ERROR", "Unsupported vault operation.")
            def prepare():
                record_id = identifier()
                if method == "sessions.create":
                    source_id = identifier()
                    source = params["source_text"].encode("utf-8")
                    metadata = {"schema_version": 1, "id": record_id, "kind": "session", "title": params["title"],
                                "source_id": source_id, "review_status": "unreviewed", "created_at": now()}
                    markdown = ("---\n" + json.dumps(metadata, ensure_ascii=False) + "\n---\n" + params["body"].replace("\r\n", "\n")).encode("utf-8")
                    source_meta = {"schema_version": 1, "id": source_id, "sha256": digest(source), "bytes": len(source), "import_kind": "pasted_text"}
                    return [("sessions/" + record_id + ".md", markdown, None),
                            ("sources/" + source_id + "/original.txt", source, None),
                            ("sources/" + source_id + "/source.json", encoded(source_meta), None)], {"id": record_id}
                if method == "captures.ingest":
                    source = params["source_text"].encode("utf-8")
                    if len(source) > 20 * 1024 * 1024:
                        raise WorkerError("LIMIT_EXCEEDED", "Captured session exceeds the supported size limit.")
                    if digest(source) != params["selected_sha256"] or params["selected_sha256"] not in params["revisions"]:
                        raise WorkerError("VALIDATION_ERROR", "Capture source identity is invalid.")
                    expected_key = digest((params["provider"] + "\0" + params["session_id"]).encode("utf-8"))
                    if expected_key != params["session_key"]:
                        raise WorkerError("VALIDATION_ERROR", "Capture session identity is invalid.")
                    receipt_path = "imports/" + params["provider"] + "/" + params["session_key"] + ".json"
                    receipt_file = owned_path(self.root, receipt_path)
                    timestamp = now()
                    if not receipt_file.exists():
                        source_id = identifier()
                        metadata = {"schema_version": 1, "id": record_id, "kind": "session", "title": params["title"],
                                    "source_id": source_id, "review_status": "unreviewed", "source_kind": "hook_capture",
                                    "provider": params["provider"], "created_at": timestamp}
                        markdown = ("---\n" + json.dumps(metadata, ensure_ascii=False) + "\n---\n").encode("utf-8")
                        source_meta = {"schema_version": 1, "id": source_id, "sha256": params["selected_sha256"],
                                       "bytes": len(source), "import_kind": "hook_capture", "provider": params["provider"],
                                       "session_key": params["session_key"], "session_id": params["session_id"],
                                       "selected_sha256": params["selected_sha256"], "revisions": sorted(params["revisions"])}
                        receipt = {"schema_version": 1, "kind": "capture_import", "provider": params["provider"],
                                   "session_key": params["session_key"], "session_id": params["session_id"],
                                   "canonical_session_id": record_id, "source_id": source_id,
                                   "selected_sha256": params["selected_sha256"], "revisions": sorted(params["revisions"]),
                                   "updated_at": timestamp}
                        return [("sessions/" + record_id + ".md", markdown, None),
                                ("sources/" + source_id + "/revisions/" + params["selected_sha256"] + ".txt", source, None),
                                ("sources/" + source_id + "/source.json", encoded(source_meta), None),
                                (receipt_path, encoded(receipt), None)], {"id": record_id, "status": "created"}
                    receipt = load(receipt_file)
                    from .service import HEX, UUID
                    revisions_shape = {"type": "array", "minItems": 1, "maxItems": 5000, "uniqueItems": True, "items": HEX}
                    receipt_shape = object_params({"schema_version": {"const": 1}, "kind": {"const": "capture_import"},
                                                   "provider": {"enum": ["claude-code", "codex"]}, "session_key": HEX,
                                                   "session_id": {"type": "string", "pattern": "^[A-Za-z0-9_-]{1,128}$"},
                                                   "canonical_session_id": UUID, "source_id": UUID, "selected_sha256": HEX,
                                                   "revisions": revisions_shape, "updated_at": {"type": "string", "format": "date-time"}})
                    if not receipt_shape.is_valid(receipt) or any(receipt.get(name) != params[name] for name in ("provider", "session_key", "session_id")):
                        raise WorkerError("CONFLICT", "Capture import identity changed; existing files were preserved.")
                    metadata = self.session_header(receipt["canonical_session_id"])
                    if metadata.get("source_id") != receipt["source_id"] or metadata.get("provider") != params["provider"] or metadata.get("source_kind") != "hook_capture":
                        raise WorkerError("CONFLICT", "Captured session metadata changed; existing files were preserved.")
                    source_meta_path = "sources/" + receipt["source_id"] + "/source.json"
                    source_meta_file = owned_path(self.root, source_meta_path)
                    source_meta = load(source_meta_file)
                    source_shape = object_params({"schema_version": {"const": 1}, "id": UUID, "sha256": HEX,
                                                  "bytes": {"type": "integer", "minimum": 0, "maximum": 20971520},
                                                  "import_kind": {"const": "hook_capture"}, "provider": {"enum": ["claude-code", "codex"]},
                                                  "session_key": HEX, "session_id": {"type": "string", "pattern": "^[A-Za-z0-9_-]{1,128}$"},
                                                  "selected_sha256": HEX, "revisions": revisions_shape})
                    if not source_shape.is_valid(source_meta) or source_meta.get("id") != receipt["source_id"] or source_meta.get("session_key") != params["session_key"]:
                        raise WorkerError("CONFLICT", "Captured source metadata changed; existing files were preserved.")
                    current_path = owned_path(self.root, "sources/" + receipt["source_id"] + "/revisions/" + source_meta["selected_sha256"] + ".txt")
                    current = current_path.read_bytes()
                    if digest(current) != source_meta["sha256"] or len(current) != source_meta["bytes"]:
                        raise WorkerError("CONFLICT", "Captured source changed; it was not overwritten.")
                    selected, selected_hash = source, params["selected_sha256"]
                    if current.startswith(source):
                        selected, selected_hash = current, source_meta["selected_sha256"]
                    elif not source.startswith(current):
                        raise WorkerError("CONFLICT", "Captured revisions diverged; existing files were preserved.")
                    revisions = sorted(set(source_meta["revisions"]) | set(params["revisions"]))
                    changed = selected_hash != source_meta["selected_sha256"] or revisions != source_meta["revisions"]
                    source_meta.update(sha256=selected_hash, bytes=len(selected), selected_sha256=selected_hash, revisions=revisions)
                    receipt.update(selected_sha256=selected_hash, revisions=revisions,
                                   updated_at=timestamp if changed else receipt["updated_at"])
                    changes = [(source_meta_path, encoded(source_meta), file_hash(source_meta_file)),
                               (receipt_path, encoded(receipt), file_hash(receipt_file))]
                    revision_path = "sources/" + receipt["source_id"] + "/revisions/" + selected_hash + ".txt"
                    revision_file = owned_path(self.root, revision_path)
                    if not revision_file.exists():
                        changes.insert(0, (revision_path, selected, None))
                    elif file_hash(revision_file) != selected_hash:
                        raise WorkerError("CONFLICT", "Captured source changed; it was not overwritten.")
                    return changes, {"id": receipt["canonical_session_id"], "status": "updated" if changed else "unchanged"}
                if method == "decisions.create":
                    timestamp = now()
                    record = {"schema_version": 1, "id": record_id, "kind": "decision", "title": params["title"], "body": params["body"],
                              "scope_ids": [], "evidence_refs": [], "provenance": "user_entered", "review_status": "unreviewed",
                              "decision_state": "proposed", "confirmation_basis": None, "revision": 1, "created_at": timestamp, "updated_at": timestamp}
                    validate("memory-record", record)
                    return [("records/" + record_id + ".json", encoded(record), None)], {"id": record_id, "revision": 1}
                record_id = params["id"]
                record = self.read_decision(record_id)
                if record["revision"] != params["expected_revision"] or record["decision_state"] != "proposed":
                    raise WorkerError("CONFLICT", "Decision changed; review it before confirming.")
                record.update(decision_state="confirmed", confirmation_basis="explicit_user_action", review_status="reviewed",
                              revision=record["revision"] + 1, updated_at=now())
                validate("memory-record", record)
                relative = "records/" + record_id + ".json"
                event = {"event": "decision_confirmed", "id": record_id, "revision": record["revision"], "at": record["updated_at"], "basis": "explicit_user_action"}
                event_path = "events/" + record_id + ".jsonl"
                return [(relative, encoded(record), file_hash(owned_path(self.root, relative))),
                        (event_path, encoded(event), None)], {"id": record_id, "revision": record["revision"]}
            return self.journal.transact(params["op_id"], {"method": method, "params": params}, prepare, after_write)
