"""Private bounded JSONL transport; stdout contains responses only."""
import json
from .errors import WorkerError
from .contracts import validate
from .journal import encoded
from .service import dispatch

MAX_FRAME = 1024 * 1024


def parse(frame):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError()
            result[key] = value
        return result
    value = json.loads(frame.decode("utf-8"), object_pairs_hook=unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    # Escaped lone surrogates are valid to Python's JSON reader but not valid UTF-8 strings.
    json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    return value


def serve(vault, incoming, outgoing):
    while True:
        frame = incoming.readline(MAX_FRAME + 1)
        if not frame:
            return 0
        request_id = None
        fatal = False
        try:
            if len(frame) > MAX_FRAME or not frame.endswith(b"\n"):
                fatal = True
                raise WorkerError("PROTOCOL_ERROR", "Invalid or oversized frame.")
            request = parse(frame)
            if isinstance(request, dict) and isinstance(request.get("id"), str) and 1 <= len(request["id"]) <= 64:
                request_id = request["id"]
            response = {"protocol_version": 1, "id": request_id, "result": dispatch(vault, request)}
        except WorkerError as error:
            response = {"protocol_version": 1, "id": request_id, "error": {"code": error.code, "message": error.message, "retryable": error.retryable}}
        except (ValueError, UnicodeError, RecursionError):
            response = {"protocol_version": 1, "id": request_id, "error": {"code": "PROTOCOL_ERROR", "message": "Invalid JSON frame.", "retryable": False}}
        except FileNotFoundError:
            response = {"protocol_version": 1, "id": request_id, "error": {"code": "NOT_FOUND", "message": "Record was not found.", "retryable": False}}
        except Exception:
            response = {"protocol_version": 1, "id": request_id, "error": {"code": "INTERNAL_ERROR", "message": "Operation failed safely; inspect local storage before retrying.", "retryable": False}}
        validate("ipc", response, "response")
        data = encoded(response)
        if len(data) > MAX_FRAME:
            data = encoded({"protocol_version": 1, "id": request_id, "error": {"code": "LIMIT_EXCEEDED", "message": "Response exceeds supported bounds.", "retryable": False}})
        outgoing.write(data)
        outgoing.flush()
        if fatal:
            return 1
