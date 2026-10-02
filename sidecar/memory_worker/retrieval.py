"""Explicit source excerpts, not semantic search or whole-vault upload."""
from .atomic_io import digest
from .errors import WorkerError
from .journal import encoded


def select(vault, selections):
    excerpts, references = [], []
    with vault.lock():
        vault.journal.recover()
        for index, selection in enumerate(selections, 1):
            state = None
            if selection["kind"] == "session":
                # Original source only: editable summaries cannot masquerade as evidence.
                record = vault.read_session(selection["id"])
                text = record["source_text"]
            else:
                # Include the manual decision state so a proposal isn't presented as approved.
                record = vault.read_decision(selection["id"])
                state = record["decision_state"]
                text = encoded(record).decode("utf-8")
            start, end = selection["start"], selection["end"]
            if end <= start or end > len(text) or end - start > 8000:
                raise WorkerError("VALIDATION_ERROR", "Selected excerpt exceeds supported bounds.")
            source_id = "S" + str(index)
            excerpt = {"source_id": source_id, "text": text[start:end]}
            if state is not None:
                excerpt.update(kind="manual_decision", decision_state=state)
            excerpts.append(excerpt)
            references.append({**selection, "source_id": source_id, "snapshot_sha256": digest(text.encode("utf-8"))})
    if sum(len(item["text"].encode("utf-8")) for item in excerpts) > 32768:
        raise WorkerError("LIMIT_EXCEEDED", "Selected excerpts exceed the total sharing limit.")
    return excerpts, references
