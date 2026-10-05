"""Known conversation fields are searchable data; setup instructions and tools are excluded."""
from __future__ import annotations

import json
import re
from typing import Iterator, NamedTuple

from .errors import WorkerError
from .session_capture import strict_json


class Passage(NamedTuple):
    text: str
    start: int
    end: int


TEXT_FIELD = re.compile(r'"(?:text|message)"\s*:\s*("(?:\\.|[^"\\])*")')


def conversation_passages(source: str, provider: str | None) -> Iterator[Passage]:
    if provider != "codex":
        for match in re.finditer(r"[^\n]+(?:\n(?!\n)[^\n]+)*", source):
            yield Passage(match.group(), match.start(), match.end())
        return
    offset = 0
    for line in source.splitlines(keepends=True):
        try:
            value = strict_json(line.encode("utf-8"))
        except WorkerError:
            offset += len(line)
            continue
        texts: set[str] = set()
        if isinstance(value, dict) and isinstance(value.get("payload"), dict):
            payload = value["payload"]
            if (value.get("type") == "response_item" and payload.get("type") == "message"
                    and payload.get("role") in {"user", "assistant"} and isinstance(payload.get("content"), list)):
                for part in payload["content"]:
                    if (isinstance(part, dict) and part.get("type") in {"input_text", "output_text"}
                            and isinstance(part.get("text"), str)):
                        texts.add(part["text"])
            elif (value.get("type") == "event_msg" and payload.get("type") in {"user_message", "agent_message"}
                  and isinstance(payload.get("message"), str)):
                texts.add(payload["message"])
        for match in TEXT_FIELD.finditer(line):
            decoded = json.loads(match.group(1))
            if decoded in texts and decoded.strip():
                yield Passage(decoded, offset + match.start(1) + 1, offset + match.end(1) - 1)
        offset += len(line)
