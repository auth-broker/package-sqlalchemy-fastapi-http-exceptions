from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.exc import DataError, DBAPIError, IntegrityError, OperationalError, ProgrammingError

from .base import DialectExceptionMapper


def _extract_sqlserver_code(exc: BaseException) -> int | None:
    # pyodbc exposes (code, message, ...) in args
    if hasattr(exc, "orig"):
        orig = exc.orig  # type: ignore[attr-defined]
        if hasattr(orig, "args"):
            args = orig.args  # type: ignore[attr-defined]
            if isinstance(args, (list, tuple)) and args:
                first = args[0]
                if isinstance(first, int):
                    return first
                if isinstance(first, str) and first.isdigit():
                    return int(first)
    return None


_MSSQL_CODE_MAP_COMMON: dict[int, tuple[int, str]] = {
    # Deadlock / lock timeout / connection
    1205: (503, "deadlock_detected"),
    1222: (503, "lock_request_timeout"),
    # Permission
    229: (403, "insufficient_privilege"),
    # Syntax
    102: (500, "syntax_error"),
    # Login/authentication failures
    18456: (503, "login_failed"),
}

_MSSQL_CODE_MAP_DATA: dict[int, tuple[int, str]] = {
    2628: (400, "string_data_right_truncation"),  # string or binary data would be truncated
    8115: (400, "numeric_value_out_of_range"),  # arithmetic overflow
    245: (400, "type_conversion_failed"),
}

_MSSQL_CODE_MAP_INTEGRITY: dict[int, tuple[int, str]] = {
    2601: (409, "unique_constraint"),  # Cannot insert duplicate key row
    2627: (409, "unique_constraint"),  # Violation of UNIQUE KEY constraint
    547: (409, "foreign_key_constraint"),  # The INSERT/UPDATE/DELETE conflicted with the REFERENCE constraint
    # NOT NULL violation can show as 515
    515: (422, "not_null_violation"),
    # CHECK violation
    547: (
        422,
        "check_violation",
    ),  # sometimes appears as 547; we already map 409 above; keep 409 for FK, 422 for CHECK ambiguous
}


def _from_code(
    code: int | None, table: dict[int, tuple[int, str]], default_status: int, default_reason: str
) -> tuple[int, Mapping[str, str]]:
    if code is not None and code in table:
        status, reason = table[code]
        return status, {"mssql": str(code), "reason": reason}
    if code is not None:
        return default_status, {"mssql": str(code), "reason": default_reason}
    return default_status, {"reason": default_reason}


class MSSQLExceptionMapper(DialectExceptionMapper):
    name = "mssql"

    def map_integrity_error(self, exc: IntegrityError):
        code = _extract_sqlserver_code(exc)
        # prefer integrity table, fall back to data/common
        if code in _MSSQL_CODE_MAP_INTEGRITY:
            return _from_code(code, _MSSQL_CODE_MAP_INTEGRITY, 409, "constraint_violation")
        if code in _MSSQL_CODE_MAP_DATA:
            return _from_code(code, _MSSQL_CODE_MAP_DATA, 409, "constraint_violation")
        return _from_code(code, _MSSQL_CODE_MAP_COMMON, 409, "constraint_violation")

    def map_operational_error(self, exc: OperationalError):
        code = _extract_sqlserver_code(exc)
        return _from_code(code, _MSSQL_CODE_MAP_COMMON, 503, "db_unavailable")

    def map_data_error(self, exc: DataError):
        code = _extract_sqlserver_code(exc)
        return _from_code(code, _MSSQL_CODE_MAP_DATA, 400, "invalid_data")

    def map_programming_error(self, exc: ProgrammingError):
        code = _extract_sqlserver_code(exc)
        return _from_code(code, _MSSQL_CODE_MAP_COMMON, 500, "db_programming_error")

    def map_dbapi_error(self, exc: DBAPIError):
        code = _extract_sqlserver_code(exc)
        return _from_code(code, _MSSQL_CODE_MAP_COMMON, 503, "db_error")
