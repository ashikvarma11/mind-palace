import datetime
import json
import uuid
from contextlib import contextmanager
import portalocker
from .atomic_io import digest, file_hash, write
from .contracts import validate, object_params
from .errors import WorkerError
from .journal import Journal, encoded, load
from .paths import no_links, owned_path, root_path


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

    def read_session(self, record_id):
        path = owned_path(self.root, "sessions/" + record_id + ".md")
        file_hash(path)
        text = path.read_text(encoding="utf-8")
        try:
            start, front, body = text.split("\n", 2)
            metadata = json.loads(front)
            if start != "---" or not body.startswith("---\n") or set(metadata) != {"schema_version", "id", "kind", "title", "source_id", "review_status", "created_at"}:
                raise ValueError()
            if metadata["schema_version"] != 1 or metadata["id"] != record_id or metadata["kind"] != "session" or metadata["review_status"] != "unreviewed":
                raise ValueError()
            from .service import UUID, TITLE
            if not object_params({"schema_version": {"const": 1}, "id": UUID, "kind": {"const": "session"},
                                  "title": TITLE, "source_id": UUID, "review_status": {"const": "unreviewed"},
                                  "created_at": {"type": "string", "format": "date-time"}}).is_valid(metadata):
                raise ValueError()
            source = owned_path(self.root, "sources/" + metadata["source_id"] + "/original.txt")
            source_meta = load(owned_path(self.root, "sources/" + metadata["source_id"] + "/source.json"))
            if not object_params({"schema_version": {"const": 1}, "id": UUID, "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                  "bytes": {"type": "integer", "minimum": 0, "maximum": 262144}, "import_kind": {"const": "pasted_text"}}).is_valid(source_meta) or source_meta["id"] != metadata["source_id"]:
                raise ValueError()
            if file_hash(source) != source_meta["sha256"] or source.stat().st_size != source_meta["bytes"]:
                raise WorkerError("CONFLICT", "Original source changed; it was not overwritten.")
            return {"metadata": metadata, "body": body[4:], "source_text": source.read_bytes().decode("utf-8")}
        except (ValueError, KeyError, TypeError):
            raise WorkerError("VALIDATION_ERROR", "Invalid session format.") from None

    def call(self, method, params, after_write=None):
        with self.lock():
            self.journal.recover()
            if method == "sessions.read":
                return self.read_session(params["id"])
            if method == "decisions.read":
                return self.read_decision(params["id"])
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
