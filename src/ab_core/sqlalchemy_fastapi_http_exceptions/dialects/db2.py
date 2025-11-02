from __future__ import annotations
from typing import Mapping, Tuple
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError, DBAPIError
from .base import DialectExceptionMapper

def _extract_sqlstate(exc: BaseException) -> str | None:
    if hasattr(exc, "orig"):
        orig = exc.orig  # type: ignore[attr-defined]
        # ibm_db_sa surfaces .sqlstate or message with SQLSTATE=xxxxx
        if hasattr(orig, "sqlstate"):
            s = orig.sqlstate  # type: ignore[attr-defined]
            if isinstance(s, str) and len(s) == 5:
                return s
        if hasattr(orig, "args"):
            args = orig.args  # type: ignore[attr-defined]
            if isinstance(args, (list, tuple)) and args:
                text = str(args[0])
                idx = text.find("SQLSTATE=")
                if idx != -1 and len(text) >= idx + 13:
                    candidate = text[idx + 9 : idx + 14]
                    if len(candidate) == 5:
                        return candidate
    return None

_DB2_INTEGRITY: dict[str, tuple[int, str]] = {
    "23505": (409, "unique_constraint"),
    "23503": (409, "foreign_key_constraint"),
    "23502": (422, "not_null_violation"),
    "23514": (422, "check_violation"),
}

_DB2_DATA: dict[str, tuple[int, str]] = {
    "22001": (400, "string_data_right_truncation"),
    "22003": (400, "numeric_value_out_of_range"),
    "22007": (400, "invalid_datetime_format"),
    "22008": (400, "datetime_field_overflow"),
}

_DB2_COMMON: dict[str, tuple[int, str]] = {
    "40001": (409, "serialization_failure"),
    "57033": (503, "lock_timeout"),        # common DB2 lock timeout state
    "08000": (503, "connection_exception"),
    "08006": (503, "connection_failure"),
    "42501": (403, "insufficient_privilege"),
    "42601": (500, "syntax_error"),
}

def _from_sqlstate(code: str | None, table: dict[str, tuple[int, str]], default_status: int, default_reason: str) -> tuple[int, Mapping[str, str]]:
    if code is not None and code in table:
        status, reason = table[code]
        return status, {"sqlstate": code, "reason": reason}
    if code is not None:
        return default_status, {"sqlstate": code, "reason": default_reason}
    return default_status, {"reason": default_reason}

class DB2ExceptionMapper(DialectExceptionMapper):
    name = "ibm_db_sa"  # SQLAlchemy commonly exposes this dialect name; adjust if needed.

    def map_integrity_error(self, exc: IntegrityError):
        code = _extract_sqlstate(exc)
        if code in _DB2_INTEGRITY:
            return _from_sqlstate(code, _DB2_INTEGRITY, 409, "constraint_violation")
        return _from_sqlstate(code, _DB2_COMMON, 409, "constraint_violation")

    def map_operational_error(self, exc: OperationalError):
        return _from_sqlstate(_extract_sqlstate(exc), _DB2_COMMON, 503, "db_unavailable")

    def map_data_error(self, exc: DataError):
        return _from_sqlstate(_extract_sqlstate(exc), _DB2_DATA, 400, "invalid_data")

    def map_programming_error(self, exc: ProgrammingError):
        return _from_sqlstate(_extract_sqlstate(exc), _DB2_COMMON, 500, "db_programming_error")

    def map_dbapi_error(self, exc: DBAPIError):
        return _from_sqlstate(_extract_sqlstate(exc), _DB2_COMMON, 503, "db_error")
