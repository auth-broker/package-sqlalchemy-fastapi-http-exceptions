from __future__ import annotations
from typing import Mapping, Tuple
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError, DBAPIError
from .base import DialectExceptionMapper

def _extract_code(exc: BaseException) -> str:
    # hdbcli often exposes text like: "[<code>] <message>" in args[0]
    if hasattr(exc, "orig"):
        orig = exc.orig  # type: ignore[attr-defined]
        if hasattr(orig, "args"):
            args = orig.args  # type: ignore[attr-defined]
            if isinstance(args, (list, tuple)) and args:
                return str(args[0])
    return ""

def _contains(s: str, needle: str) -> bool:
    return needle.lower() in s.lower()

class HANAExceptionMapper(DialectExceptionMapper):
    name = "hana"

    def map_integrity_error(self, exc: IntegrityError):
        msg = _extract_code(exc)
        if _contains(msg, "unique constraint"):
            return 409, {"reason": "unique_constraint"}
        if _contains(msg, "foreign key"):
            return 409, {"reason": "foreign_key_constraint"}
        if _contains(msg, "not null"):
            return 422, {"reason": "not_null_violation"}
        if _contains(msg, "check constraint"):
            return 422, {"reason": "check_violation"}
        return 409, {"reason": "constraint_violation"}

    def map_operational_error(self, exc: OperationalError):
        msg = _extract_code(exc)
        if _contains(msg, "lock timeout") or _contains(msg, "deadlock"):
            return 503, {"reason": "lock_or_deadlock"}
        if _contains(msg, "connection") or _contains(msg, "network"):
            return 503, {"reason": "connection_exception"}
        return 503, {"reason": "db_unavailable"}

    def map_data_error(self, exc: DataError):
        msg = _extract_code(exc)
        if _contains(msg, "value too large") or _contains(msg, "overflow"):
            return 400, {"reason": "numeric_value_out_of_range"}
        if _contains(msg, "invalid date") or _contains(msg, "date/time"):
            return 400, {"reason": "invalid_datetime_format"}
        if _contains(msg, "too long"):
            return 400, {"reason": "string_data_right_truncation"}
        return 400, {"reason": "invalid_data"}

    def map_programming_error(self, exc: ProgrammingError):
        msg = _extract_code(exc)
        if _contains(msg, "not authorized") or _contains(msg, "insufficient privilege"):
            return 403, {"reason": "insufficient_privilege"}
        if _contains(msg, "syntax error"):
            return 500, {"reason": "syntax_error"}
        return 500, {"reason": "db_programming_error"}

    def map_dbapi_error(self, exc: DBAPIError):
        msg = _extract_code(exc)
        if _contains(msg, "lock") or _contains(msg, "timeout"):
            return 503, {"reason": "db_error_lock_or_timeout"}
        return 503, {"reason": "db_error"}
