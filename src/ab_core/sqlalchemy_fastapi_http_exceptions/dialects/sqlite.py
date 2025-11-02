from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.exc import DataError, DBAPIError, IntegrityError, OperationalError, ProgrammingError

from .base import DialectExceptionMapper


def _orig_message(exc: BaseException) -> str:
    if hasattr(exc, "orig"):
        orig = exc.orig  # type: ignore[attr-defined]
        # sqlite3.Error often has .args[0] as message
        if hasattr(orig, "args"):
            args = orig.args  # type: ignore[attr-defined]
            if isinstance(args, (list, tuple)) and args:
                first = args[0]
                if isinstance(first, str):
                    return first
    return ""


def _reason_from_message(msg: str) -> tuple[int, str] | None:
    # SQLite strings are fairly consistent
    if "UNIQUE constraint failed" in msg:
        return (409, "unique_constraint")
    if "FOREIGN KEY constraint failed" in msg:
        return (409, "foreign_key_constraint")
    if "NOT NULL constraint failed" in msg:
        return (422, "not_null_violation")
    if "CHECK constraint failed" in msg:
        return (422, "check_violation")
    return None


class SQLiteExceptionMapper(DialectExceptionMapper):
    name = "sqlite"

    def map_integrity_error(self, exc: IntegrityError):
        msg = _orig_message(exc)
        deduced = _reason_from_message(msg)
        if deduced:
            status, reason = deduced
            extra: Mapping[str, str] = {"reason": reason}
            return status, extra
        return 409, {"reason": "constraint_violation"}

    def map_operational_error(self, exc: OperationalError):
        # DB locked / busy often appears here; treat as transient
        msg = _orig_message(exc)
        if "database is locked" in msg or "database is busy" in msg:
            return 503, {"reason": "db_locked"}
        return 503, {"reason": "db_unavailable"}

    def map_data_error(self, _exc: DataError):
        return 400, {"reason": "invalid_data"}

    def map_programming_error(self, exc: ProgrammingError):
        # Typically malformed SQL
        return 500, {"reason": "db_programming_error"}

    def map_dbapi_error(self, _exc: DBAPIError):
        return 503, {"reason": "db_error"}
