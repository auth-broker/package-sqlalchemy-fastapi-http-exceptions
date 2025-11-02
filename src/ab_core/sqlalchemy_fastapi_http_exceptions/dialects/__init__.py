from .base import DialectExceptionMapper, GenericExceptionMapper
from .postgres import PostgresExceptionMapper
from .mysql import MySQLExceptionMapper
from .sqlite import SQLiteExceptionMapper
from .mssql import MSSQLExceptionMapper
from .oracle import OracleExceptionMapper
from .db2 import DB2ExceptionMapper
from .hana import HANAExceptionMapper
from .ansi import AnsiSQLStateMapper  # optional, generic

_DIALECTS: tuple[DialectExceptionMapper, ...] = (
    PostgresExceptionMapper(),
    MySQLExceptionMapper(),
    SQLiteExceptionMapper(),
    MSSQLExceptionMapper(),
    OracleExceptionMapper(),
    DB2ExceptionMapper(),
    HANAExceptionMapper(),
    AnsiSQLStateMapper(),
    GenericExceptionMapper(),   # final fallback
)

def get_mapper_by_name(name: str | None) -> DialectExceptionMapper:
    if name:
        lowered = name.lower()
        for mapper in _DIALECTS:
            if mapper.name == lowered:
                return mapper
    return _DIALECTS[-1]
