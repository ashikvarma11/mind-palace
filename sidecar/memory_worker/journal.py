"""Recoverable file transactions. Caller must hold the vault's OS lock."""
import base64
import json
import re
from .atomic_io import digest, file_hash, write
from .errors import WorkerError
from .paths import ID, no_links, owned_path


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def load(path):
    file_hash(path)  # Reject links, directories and oversized stored content.
    try:
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError()
                result[key] = value
            return result
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError):
        raise WorkerError("VALIDATION_ERROR", "Stored JSON is invalid.") from None


class Journal:
    def __init__(self, root):
        self.root = root
        self.directory = root / ".memory/journal"
        no_links(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def apply(self, path, after_write=None):
        intent = load(path)
        if not isinstance(intent, dict) or set(intent) != {"version", "fingerprint", "entries", "result", "done"}:
            raise WorkerError("VALIDATION_ERROR", "Invalid recovery journal.")
        if intent["version"] != 1 or type(intent["done"]) is not bool or not isinstance(intent["result"], dict):
            raise WorkerError("VALIDATION_ERROR", "Invalid recovery journal.")
        if not isinstance(intent["fingerprint"], str) or not re.fullmatch(r"[0-9a-f]{64}", intent["fingerprint"]):
            raise WorkerError("VALIDATION_ERROR", "Invalid recovery journal.")
        entries = intent["entries"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= 4:
            raise WorkerError("VALIDATION_ERROR", "Invalid recovery journal.")
        prepared = []
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"path", "old", "new", "data"}:
                raise WorkerError("VALIDATION_ERROR", "Invalid recovery journal.")
            target = owned_path(self.root, entry["path"])
            if entry["old"] is not None and (not isinstance(entry["old"], str) or not re.fullmatch(r"[0-9a-f]{64}", entry["old"])):
                raise WorkerError("VALIDATION_ERROR", "Invalid recovery journal.")
            try:
                data = base64.b64decode(entry["data"], validate=True)
            except (ValueError, TypeError):
                raise WorkerError("VALIDATION_ERROR", "Invalid recovery journal.") from None
            if len(data) > 20 * 1024 * 1024 or digest(data) != entry["new"] or target in [item[0] for item in prepared]:
                raise WorkerError("VALIDATION_ERROR", "Invalid recovery journal.")
            prepared.append((target, data, entry["old"], entry["new"]))
        if not intent["done"]:
            # Check every target before writing any, preserving externally changed files.
            for target, data, old, new in prepared:
                if file_hash(target) not in (old, new):
                    raise WorkerError("CONFLICT", "Recovery found changed content; all versions were preserved.")
            for index, (target, data, old, new) in enumerate(prepared):
                if file_hash(target) != new:
                    write(target, data, old)
                if after_write:
                    after_write(index)
            previous = file_hash(path)
            intent["done"] = True
            write(path, encoded(intent), previous)
        return intent

    def recover(self):
        for path in sorted(self.directory.iterdir()):
            no_links(path)
            if not re.fullmatch(ID + r"\.json", path.name):
                raise WorkerError("VALIDATION_ERROR", "Unexpected recovery journal entry.")
            self.apply(path)

    def transact(self, op_id, request, prepare, after_write=None):
        if not re.fullmatch(ID, op_id):
            raise WorkerError("VALIDATION_ERROR", "Invalid operation identifier.")
        fingerprint = digest(encoded(request))
        path = self.directory / (op_id + ".json")
        if path.exists():
            intent = self.apply(path)
            if intent["fingerprint"] != fingerprint:
                raise WorkerError("CONFLICT", "Operation identifier was already used.")
            return intent["result"]
        changes, result = prepare()
        entries = [{"path": relative, "old": old, "new": digest(data),
                    "data": base64.b64encode(data).decode("ascii")} for relative, data, old in changes]
        intent = {"version": 1, "fingerprint": fingerprint, "entries": entries, "result": result, "done": False}
        if len(encoded(intent)) > 64 * 1024 * 1024:
            raise WorkerError("VALIDATION_ERROR", "Operation exceeds storage bounds.")
        write(path, encoded(intent), None)
        return self.apply(path, after_write)["result"]
