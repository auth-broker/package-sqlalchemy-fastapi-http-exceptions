from .base import DialectExceptionMapper, GenericExceptionMapper
from .postgres import PostgresExceptionMapper

# Immutable registry
_DIALECTS: tuple[DialectExceptionMapper, ...] = (
    PostgresExceptionMapper(),
    GenericExceptionMapper(),  # keep last as fallback
)


def get_mapper_by_name(name: str | None) -> DialectExceptionMapper:
    if name:
        lowered = name.lower()
        for mapper in _DIALECTS:
            if mapper.name == lowered:
                return mapper
    # explicit fallback, not silent
    return _DIALECTS[-1]
