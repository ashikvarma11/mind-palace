import json
import datetime
import re
from pathlib import Path
import sys
from jsonschema import Draft202012Validator, FormatChecker
from .errors import WorkerError

SCHEMAS = Path(sys._MEIPASS) / "schemas" if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2] / "schemas"
FORMATS = FormatChecker()


@FORMATS.checks("date-time", raises=(ValueError, TypeError))
def utc_timestamp(value):
    # The vault contract uses UTC Z timestamps, not arbitrary timezone offsets.
    if not isinstance(value, str):
        return True
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value, flags=re.ASCII):
        return False
    return datetime.datetime.fromisoformat(value).utcoffset() == datetime.timedelta(0)


def validate(name, value, definition=None):
    schema = json.loads((SCHEMAS / (name + ".schema.json")).read_text(encoding="utf-8"))
    if definition:
        schema = {"$ref": "#/$defs/" + definition, "$defs": schema["$defs"]}
    Draft202012Validator.check_schema(schema)
    if not Draft202012Validator(schema, format_checker=FORMATS).is_valid(value):
        raise WorkerError("VALIDATION_ERROR", "Input or stored format is invalid.")


def object_params(properties, required=None):
    return Draft202012Validator({"type": "object", "properties": properties,
                                "required": list(properties) if required is None else required,
                                "additionalProperties": False}, format_checker=FORMATS)
