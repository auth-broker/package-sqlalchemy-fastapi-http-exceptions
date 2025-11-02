from .base import DialectExceptionMapper, GenericExceptionMapper
from .mssql import MSSQLExceptionMapper
from .mysql import MySQLExceptionMapper
from .oracle import OracleExceptionMapper
from .postgres import PostgresExceptionMapper
from .sqlite import SQLiteExceptionMapper

_DIALECTS: tuple[DialectExceptionMapper, ...] = (
    PostgresExceptionMapper(),
    MySQLExceptionMapper(),  # covers MySQL & MariaDB SA dialects (“mysql”, “mariadb” both surface as “mysql” in SA)
    SQLiteExceptionMapper(),
    MSSQLExceptionMapper(),
    OracleExceptionMapper(),
    GenericExceptionMapper(),  # fallback
)


def get_mapper_by_name(name: str | None) -> DialectExceptionMapper:
    if name:
        lowered = name.lower()
        for mapper in _DIALECTS:
            if mapper.name == lowered:
                return mapper
    return _DIALECTS[-1]
