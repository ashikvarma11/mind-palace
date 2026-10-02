from .contracts import object_params, validate
from .errors import WorkerError
from .paths import ID

UUID = {"type": "string", "pattern": "^" + ID + "$"}
TEXT = {"type": "string", "maxLength": 32768}
TITLE = {"type": "string", "minLength": 1, "maxLength": 200}
PARAMS = {
    "health": object_params({}),
    "sessions.create": object_params({"op_id": UUID, "title": TITLE, "body": TEXT, "source_text": {"type": "string", "maxLength": 65536}}),
    "sessions.read": object_params({"id": UUID}),
    "sessions.list": object_params({"limit": {"type": "integer", "minimum": 1, "maximum": 50},
                                    "offset": {"type": "integer", "minimum": 0, "maximum": 1000}}),
    "decisions.create": object_params({"op_id": UUID, "title": TITLE, "body": TEXT}),
    "decisions.read": object_params({"id": UUID}),
    "decisions.confirm": object_params({"op_id": UUID, "id": UUID, "expected_revision": {"type": "integer", "minimum": 1}, "confirm": {"const": True}}),
}


def dispatch(vault, request):
    validate("ipc", request)
    method, params = request["method"], request["params"]
    if method.startswith("cloud."):
        if method == "cloud.preview":
            return vault.previews.preview(vault, params)
        if method == "cloud.prepare":
            return vault.previews.prepare(vault, params)
        return vault.previews.discard(params)
    if not PARAMS[method].is_valid(params):
        raise WorkerError("VALIDATION_ERROR", "Method parameters are invalid.")
    if method == "health":
        return {"version": "0.1.0", "storage": "foundation", "ai_enabled": False}
    return vault.call(method, params)
