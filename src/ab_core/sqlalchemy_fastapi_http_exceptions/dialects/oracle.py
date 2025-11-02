from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.exc import DataError, DBAPIError, IntegrityError, OperationalError, ProgrammingError

from .base import DialectExceptionMapper


def _extract_ora_code(exc: BaseException) -> int | None:
    # cx_Oracle/oracledb: orig has .code (int) and .message (str)
    if hasattr(exc, "orig"):
        orig = exc.orig  # type: ignore[attr-defined]
        if hasattr(orig, "code"):
            code = orig.code  # type: ignore[attr-defined]
            if isinstance(code, int):
                return code
            if isinstance(code, str) and code.startswith("ORA-") and code[4:9].isdigit():
                return int(code[4:9])
        # fallback: try parse from args/message if present
        if hasattr(orig, "message"):
            msg = orig.message  # type: ignore[attr-defined]
            if isinstance(msg, str) and "ORA-" in msg:
                idx = msg.find("ORA-")
                if idx != -1 and len(msg) >= idx + 9 and msg[idx + 4 : idx + 9].isdigit():
                    return int(msg[idx + 4 : idx + 9])
        if hasattr(orig, "args"):
            args = orig.args  # type: ignore[attr-defined]
            if isinstance(args, (list, tuple)) and args:
                s = str(args[0])
                if "ORA-" in s:
                    idx = s.find("ORA-")
                    if idx != -1 and len(s) >= idx + 9 and s[idx + 4 : idx + 9].isdigit():
                        return int(s[idx + 4 : idx + 9])
    return None


_ORA_INTEGRITY: dict[int, tuple[int, str]] = {
    1: (409, "unique_constraint"),  # ORA-00001
    2291: (409, "foreign_key_constraint"),  # ORA-02291 integrity constraint violated - parent key not found
    2292: (409, "foreign_key_constraint"),  # ORA-02292 child record found
    1400: (422, "not_null_violation"),  # ORA-01400 cannot insert NULL
    2290: (422, "check_violation"),  # ORA-02290 check constraint violated
}

_ORA_OPERATIONAL: dict[int, tuple[int, str]] = {
    60: (503, "deadlock_detected"),  # ORA-00060
    12541: (503, "no_listener"),  # ORA-12541
    12514: (503, "listener_could_not_resolve"),
}

_ORA_DATA: dict[int, tuple[int, str]] = {
    1438: (400, "numeric_value_out_of_range"),  # ORA-01438
    1861: (400, "invalid_datetime_format"),  # ORA-01861
    12899: (400, "string_data_right_truncation"),  # ORA-12899 value too large for column
}

_ORA_PROGRAMMING: dict[int, tuple[int, str]] = {
    900: (500, "syntax_error"),  # ORA-00900 invalid SQL statement
    933: (500, "syntax_error"),  # ORA-00933 SQL command not properly ended
    1031: (403, "insufficient_privilege"),  # ORA-01031
}


def _from_ora(
    code: int | None, table: dict[int, tuple[int, str]], default_status: int, default_reason: str
) -> tuple[int, Mapping[str, str]]:
    if code is not None and code in table:
        status, reason = table[code]
        return status, {"oracle": f"ORA-{code:05d}", "reason": reason}
    if code is not None:
        return default_status, {"oracle": f"ORA-{code:05d}", "reason": default_reason}
    return default_status, {"reason": default_reason}


class OracleExceptionMapper(DialectExceptionMapper):
    name = "oracle"

    def map_integrity_error(self, exc: IntegrityError):
        return _from_ora(_extract_ora_code(exc), _ORA_INTEGRITY, 409, "constraint_violation")

    def map_operational_error(self, exc: OperationalError):
        return _from_ora(_extract_ora_code(exc), _ORA_OPERATIONAL, 503, "db_unavailable")

    def map_data_error(self, exc: DataError):
        return _from_ora(_extract_ora_code(exc), _ORA_DATA, 400, "invalid_data")

    def map_programming_error(self, exc: ProgrammingError):
        return _from_ora(_extract_ora_code(exc), _ORA_PROGRAMMING, 500, "db_programming_error")

    def map_dbapi_error(self, exc: DBAPIError):
        # use union of the above as a pragmatic catch-all
        code = _extract_ora_code(exc)
        if code is not None:
            for table in (_ORA_INTEGRITY, _ORA_OPERATIONAL, _ORA_DATA, _ORA_PROGRAMMING):
                if code in table:
                    return _from_ora(code, table, 503, "db_error")
        return _from_ora(code, {}, 503, "db_error")
