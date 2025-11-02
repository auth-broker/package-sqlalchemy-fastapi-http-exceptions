from __future__ import annotations
from typing import Mapping, Tuple
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError, DBAPIError
from .base import DialectExceptionMapper

def _sqlstate(exc: BaseException) -> str | None:
    if hasattr(exc, "orig"):
        orig = exc.orig  # type: ignore[attr-defined]
        if hasattr(orig, "sqlstate"):
            s = orig.sqlstate  # type: ignore[attr-defined]
            if isinstance(s, str) and len(s) == 5:
                return s
        if hasattr(orig, "diag") and hasattr(orig.diag, "sqlstate"):
            s2 = orig.diag.sqlstate  # type: ignore[attr-defined]
            if isinstance(s2, str) and len(s2) == 5:
                return s2
    return None

_SPECIFICS: dict[str, tuple[int, str]] = {
    "23505": (409, "unique_constraint"),
    "23503": (409, "foreign_key_constraint"),
    "23502": (422, "not_null_violation"),
    "23514": (422, "check_violation"),
    "42501": (403, "insufficient_privilege"),
    "42601": (500, "syntax_error"),
    "40P01": (503, "deadlock_detected"),   # PG-flavoured, but safe if seen
    "40001": (409, "serialization_failure"),
}

def _class_default(sqlstate: str) -> tuple[int, str]:
    c = sqlstate[:2]
    if c == "23":   # Integrity
        return (409, "constraint_violation")
    if c == "22":   # Data
        return (400, "invalid_data")
    if c == "40":   # Txn rollback
        return (409, "transaction_rollback")
    if c == "08":   # Connection
        return (503, "connection_exception")
    if c == "57":   # Operator intervention
        return (503, "operator_intervention")
    if c == "42":   # Syntax/Access
        return (500, "syntax_or_access_rule")
    return (500, "db_error")

def _map(sqlstate: str | None, default_status: int, default_reason: str) -> tuple[int, Mapping[str, str]]:
    if sqlstate is None:
        return default_status, {"reason": default_reason}
    if sqlstate in _SPECIFICS:
        status, reason = _SPECIFICS[sqlstate]
        return status, {"sqlstate": sqlstate, "reason": reason}
    status, reason = _class_default(sqlstate)
    return status, {"sqlstate": sqlstate, "reason": reason}

class AnsiSQLStateMapper(DialectExceptionMapper):
    name = "ansi-sqlstate"  # not a real SA dialect; treat as a generic mapper

    def map_integrity_error(self, exc: IntegrityError):
        return _map(_sqlstate(exc), 409, "constraint_violation")

    def map_operational_error(self, exc: OperationalError):
        return _map(_sqlstate(exc), 503, "db_unavailable")

    def map_data_error(self, exc: DataError):
        return _map(_sqlstate(exc), 400, "invalid_data")

    def map_programming_error(self, exc: ProgrammingError):
        return _map(_sqlstate(exc), 500, "db_programming_error")

    def map_dbapi_error(self, exc: DBAPIError):
        return _map(_sqlstate(exc), 503, "db_error")
