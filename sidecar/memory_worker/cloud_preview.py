"""In-memory consent-bound preparation. There is deliberately no send method."""
import copy
import time
import uuid
from .atomic_io import digest
from .contracts import validate
from .errors import WorkerError
from .journal import encoded
from .retrieval import select


class Previews:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.pending = {}

    def _prune(self):
        now = self.clock()
        self.pending = {key: value for key, value in self.pending.items() if value["expires"] > now}

    def preview(self, vault, params):
        validate("cloud-ai", params, "preview")
        self._prune()
        if len(self.pending) >= 8:
            raise WorkerError("BUSY", "Too many previews; discard one before continuing.", True)
        excerpts, references = select(vault, params["selections"])
        # Lazy import prevents a circular protocol/service/provider import at startup.
        from .cloud_contracts import build
        request = build(params["provider"], params["model"], params["question"], params["max_output_tokens"], excerpts)
        sha = digest(encoded(request))
        preview_id = str(uuid.uuid4())
        self.pending[preview_id] = {"request": request, "sha": sha, "references": references,
                                    "expires": self.clock() + 300}
        return {"preview_id": preview_id, "payload_sha256": sha, "expires_in_seconds": 300,
                "request": copy.deepcopy(request), "local_references": copy.deepcopy(references),
                "sharing_warning": "Only the displayed request would be sent to the chosen provider. Provider retention and API charges apply.",
                "can_send": False}

    def prepare(self, vault, params):
        validate("cloud-ai", params, "prepare")
        self._prune()
        entry = self.pending.get(params["preview_id"])
        if entry is None or entry["sha"] != params["payload_sha256"]:
            raise WorkerError("CONFLICT", "Preview expired, changed or was already consumed.")
        # Re-read source hashes: edits after preview require a new review, not silently different input.
        selections = [{key: reference[key] for key in ("kind", "id", "start", "end")} for reference in entry["references"]]
        _, current = select(vault, selections)
        if current != entry["references"]:
            self.pending.pop(params["preview_id"], None)
            raise WorkerError("CONFLICT", "Source changed since preview; review a new preview.")
        self.pending.pop(params["preview_id"], None)
        return {"request": copy.deepcopy(entry["request"]), "payload_sha256": entry["sha"],
                "local_references": copy.deepcopy(entry["references"]), "can_send": False,
                "status": "prepared_only_native_transport_unavailable"}

    def discard(self, params):
        validate("cloud-ai", params, "discard")
        self.pending.pop(params["preview_id"], None)
        return {"discarded": True}
