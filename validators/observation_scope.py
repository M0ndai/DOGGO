"""Companion timing check for structurally valid ObservationScope instances.

This function reads only its argument. It does not collect evidence, resolve
references, change scope, or perform external actions. JSON Schema validation
remains required for the complete closed structural contract.
"""

from datetime import datetime
import re


TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt](?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]{1,6})?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])\Z"
)


def _timestamp(value):
    if not isinstance(value, str) or not TIMESTAMP.fullmatch(value):
        return None
    # RFC 3339's -00:00 denotes an unknown offset, not a known UTC instant.
    if value.endswith("-00:00"):
        return None
    try:
        return datetime.fromisoformat(value.upper().replace("Z", "+00:00"))
    except ValueError:
        return None


def validate_scope_time(scope):
    """Return timing errors; an empty list means only timing checks passed.

    Require calendar-valid timestamps with known offsets and end >= start.
    Leap seconds and precision beyond microseconds fail closed. Missing or
    malformed timing structures produce errors rather than exceptions.
    """
    if not isinstance(scope, dict):
        return ["scope must be an object"]
    errors = []
    if _timestamp(scope.get("collection_time")) is None:
        errors.append("collection_time must be a supported timestamp with a known offset")
    window = scope.get("time_window")
    if not isinstance(window, dict):
        errors.append("time_window must be an object")
        return errors
    start = _timestamp(window.get("start"))
    end = _timestamp(window.get("end"))
    for field, stamp in (("start", start), ("end", end)):
        if stamp is None:
            errors.append(f"time_window.{field} must be a supported timestamp with a known offset")
    if start is not None and end is not None and end < start:
        errors.append("time_window.end must not precede time_window.start")
    return errors
