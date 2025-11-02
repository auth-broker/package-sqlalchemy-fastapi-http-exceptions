from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.exc import DataError, DBAPIError, IntegrityError, OperationalError, ProgrammingError

from .base import DialectExceptionMapper


def _extract_sqlstate(exc: BaseException) -> str | None:
    # No getattr/try: check attribute presence explicitly
    if hasattr(exc, "orig"):
        orig = exc.orig  # type: ignore[attr-defined]
        if hasattr(orig, "diag") and hasattr(orig.diag, "sqlstate"):
            sqlstate = orig.diag.sqlstate  # type: ignore[attr-defined]
            if sqlstate:
                return sqlstate
        if hasattr(orig, "pgcode") and orig.pgcode:  # type: ignore[attr-defined]
            return orig.pgcode  # type: ignore[attr-defined]
        if hasattr(orig, "sqlstate") and orig.sqlstate:  # type: ignore[attr-defined]
            return orig.sqlstate  # type: ignore[attr-defined]
    return None


# Integrity/operational/programming common map
_PG_SQLSTATE_MAP_INT: dict[str, tuple[int, str]] = {
    # Class 23 — Integrity Constraint Violation
    "23505": (409, "unique_constraint"),
    "23503": (409, "foreign_key_constraint"),
    "23502": (422, "not_null_violation"),
    "23514": (422, "check_violation"),
    "23P01": (409, "exclusion_violation"),
    # Class 40 — Transaction Rollback
    "40001": (409, "serialization_failure"),
    "40P01": (503, "deadlock_detected"),
    # Class 08 — Connection Exception
    "08006": (503, "connection_failure"),
    "08000": (503, "connection_exception"),
    # Class 57 — Operator Intervention
    "57P01": (503, "admin_shutdown"),
    "57P02": (503, "crash_shutdown"),
    "57P03": (503, "cannot_connect_now"),
    # Class 42 — Syntax/Error or Access Rule Violation
    "42601": (500, "syntax_error"),
    "42501": (403, "insufficient_privilege"),
}

# DataErrors
_PG_SQLSTATE_MAP_DATA: dict[str, tuple[int, str]] = {
    "22001": (400, "string_data_right_truncation"),
    "22003": (400, "numeric_value_out_of_range"),
    "22007": (400, "invalid_datetime_format"),
    "22008": (400, "datetime_field_overflow"),
    "2200G": (400, "most_specific_type_mismatch"),
}


def _from_map(
    code: str | None, table: dict[str, tuple[int, str]], default_status: int, default_reason: str
) -> tuple[int, Mapping[str, str]]:
    if code and code in table:
        status, reason = table[code]
        return status, {"sqlstate": code, "reason": reason}
    if code:
        return default_status, {"sqlstate": code, "reason": default_reason}
    return default_status, {"reason": default_reason}


class PostgresExceptionMapper(DialectExceptionMapper):
    name = "postgresql"

    def map_integrity_error(self, exc: IntegrityError):
        return _from_map(_extract_sqlstate(exc), _PG_SQLSTATE_MAP_INT, 409, "constraint_violation")

    def map_operational_error(self, exc: OperationalError):
        return _from_map(_extract_sqlstate(exc), _PG_SQLSTATE_MAP_INT, 503, "db_unavailable")

    def map_data_error(self, exc: DataError):
        return _from_map(_extract_sqlstate(exc), _PG_SQLSTATE_MAP_DATA, 400, "invalid_data")

    def map_programming_error(self, exc: ProgrammingError):
        return _from_map(_extract_sqlstate(exc), _PG_SQLSTATE_MAP_INT, 500, "db_programming_error")

    def map_dbapi_error(self, exc: DBAPIError):
        return _from_map(_extract_sqlstate(exc), _PG_SQLSTATE_MAP_INT, 503, "db_error")
