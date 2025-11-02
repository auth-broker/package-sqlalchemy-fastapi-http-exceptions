from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.exc import DataError, DBAPIError, IntegrityError, OperationalError, ProgrammingError

from .base import DialectExceptionMapper


def _extract_errno(exc: BaseException) -> int | None:
    # MySQLdb / PyMySQL put (errno, msg, ...) in orig.args
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


# Key MySQL/MariaDB errnos
_MY_ERRNO_TO_STATUS_REASON: dict[int, tuple[int, str]] = {
    # Integrity
    1062: (409, "unique_constraint"),  # Duplicate entry
    1452: (409, "foreign_key_constraint"),  # Cannot add or update child row
    1048: (422, "not_null_violation"),
    3819: (422, "check_violation"),  # Check constraint failed (MySQL 8+)
    # Operational / availability / locking
    1213: (503, "deadlock_detected"),
    1205: (503, "lock_wait_timeout"),
    1040: (503, "too_many_connections"),
    2006: (503, "mysql_server_gone"),
    # Permissions / syntax
    1142: (403, "insufficient_privilege"),  # command denied to user
    1143: (403, "insufficient_privilege"),  # column access denied
    1064: (500, "syntax_error"),
}

# Data errors
_MY_DATA_ERRNO: dict[int, tuple[int, str]] = {
    1406: (400, "string_data_right_truncation"),  # Data too long
    1264: (400, "numeric_value_out_of_range"),
    1292: (400, "invalid_datetime_format"),  # Incorrect datetime value
    1366: (400, "invalid_string_value"),  # Incorrect string value / collation
}


def _from_errno(
    errno: int | None, table: dict[int, tuple[int, str]], default_status: int, default_reason: str
) -> tuple[int, Mapping[str, str]]:
    if errno is not None and errno in table:
        status, reason = table[errno]
        return status, {"errno": str(errno), "reason": reason}
    if errno is not None:
        return default_status, {"errno": str(errno), "reason": default_reason}
    return default_status, {"reason": default_reason}


class MySQLExceptionMapper(DialectExceptionMapper):
    name = "mysql"  # also used by MariaDB dialects in SA

    def map_integrity_error(self, exc: IntegrityError):
        errno = _extract_errno(exc)
        # merge integrity + general table to catch FK, NOT NULL, etc.
        merged = dict(_MY_ERRNO_TO_STATUS_REASON)
        merged.update({k: v for k, v in _MY_DATA_ERRNO.items() if k in (1048, 3819)})
        return _from_errno(errno, merged, 409, "constraint_violation")

    def map_operational_error(self, exc: OperationalError):
        errno = _extract_errno(exc)
        return _from_errno(errno, _MY_ERRNO_TO_STATUS_REASON, 503, "db_unavailable")

    def map_data_error(self, exc: DataError):
        errno = _extract_errno(exc)
        return _from_errno(errno, _MY_DATA_ERRNO, 400, "invalid_data")

    def map_programming_error(self, exc: ProgrammingError):
        errno = _extract_errno(exc)
        return _from_errno(errno, _MY_ERRNO_TO_STATUS_REASON, 500, "db_programming_error")

    def map_dbapi_error(self, exc: DBAPIError):
        errno = _extract_errno(exc)
        return _from_errno(errno, _MY_ERRNO_TO_STATUS_REASON, 503, "db_error")
