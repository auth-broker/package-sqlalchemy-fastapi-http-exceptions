from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

from sqlalchemy.exc import DataError, DBAPIError, IntegrityError, OperationalError, ProgrammingError


class DialectExceptionMapper(ABC):
    """Interface for dialect-specific DB -> HTTP mappings."""

    name: str = "generic"

    @abstractmethod
    def map_integrity_error(self, exc: IntegrityError) -> tuple[int, Mapping[str, str]]: ...

    @abstractmethod
    def map_operational_error(self, exc: OperationalError) -> tuple[int, Mapping[str, str]]: ...

    @abstractmethod
    def map_data_error(self, exc: DataError) -> tuple[int, Mapping[str, str]]: ...

    @abstractmethod
    def map_programming_error(self, exc: ProgrammingError) -> tuple[int, Mapping[str, str]]: ...

    @abstractmethod
    def map_dbapi_error(self, exc: DBAPIError) -> tuple[int, Mapping[str, str]]: ...


class GenericExceptionMapper(DialectExceptionMapper):
    name = "generic"

    def map_integrity_error(self, _exc: IntegrityError) -> tuple[int, Mapping[str, str]]:
        return 409, {"reason": "constraint_violation"}

    def map_operational_error(self, _exc: OperationalError) -> tuple[int, Mapping[str, str]]:
        return 503, {"reason": "db_unavailable"}

    def map_data_error(self, _exc: DataError) -> tuple[int, Mapping[str, str]]:
        return 400, {"reason": "invalid_data"}

    def map_programming_error(self, _exc: ProgrammingError) -> tuple[int, Mapping[str, str]]:
        return 500, {"reason": "db_programming_error"}

    def map_dbapi_error(self, _exc: DBAPIError) -> tuple[int, Mapping[str, str]]:
        return 503, {"reason": "db_error"}
