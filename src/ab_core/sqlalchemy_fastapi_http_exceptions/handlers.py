import logging
import reprlib
from collections.abc import Mapping
from typing import Annotated

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import (
    DataError,
    DBAPIError,
    IntegrityError,
    MultipleResultsFound,
    NoResultFound,
    OperationalError,
    ProgrammingError,
)

from ab_core.database.databases import Database
from ab_core.dependency import Depends, inject

from .dialects import DialectExceptionMapper, get_mapper_by_name

logger = logging.getLogger(__name__)


def _payload(message: str, *, error: BaseException, extra: Mapping[str, str]) -> dict:
    short = reprlib.Repr()
    short.maxstring = 160
    return {"detail": message, "error": short.repr(error), **extra}


def _map_with_dialect(
    db: Database,
    exc: BaseException,
    default_status: int,
    default_reason: str,
) -> tuple[int, Mapping[str, str]]:
    mapper: DialectExceptionMapper = get_mapper_by_name(db.async_engine.dialect.name)

    if isinstance(exc, IntegrityError):
        status, extra = mapper.map_integrity_error(exc)
    elif isinstance(exc, OperationalError):
        status, extra = mapper.map_operational_error(exc)
    elif isinstance(exc, DataError):
        status, extra = mapper.map_data_error(exc)
    elif isinstance(exc, ProgrammingError):
        status, extra = mapper.map_programming_error(exc)
    elif isinstance(exc, DBAPIError):
        status, extra = mapper.map_dbapi_error(exc)
    else:
        # Fallback for unexpected subclasses: use provided defaults
        status, extra = default_status, {"reason": default_reason}

    # Post-condition guard
    if not isinstance(status, int) or not isinstance(extra, Mapping):
        return default_status, {"reason": default_reason}
    return status, extra


@inject
async def integrity_error_handler(
    _request: Request,
    exc: IntegrityError,
    db: Annotated[Database, Depends(Database, persist=True)],
):
    logger.error("Constraint violation", exc_info=exc)
    status, extra = _map_with_dialect(
        db=db,
        exc=exc,
        default_status=409,
        default_reason="constraint_violation",
    )
    return JSONResponse(status_code=status, content=_payload("Constraint violation", error=exc, extra=extra))


@inject
async def operational_error_handler(
    _req: Request,
    exc: OperationalError,
    db: Annotated[Database, Depends(Database, persist=True)],
):
    logger.error("Database temporarily unavailable", exc_info=exc)
    status, extra = _map_with_dialect(
        db=db,
        exc=exc,
        default_status=503,
        default_reason="db_unavailable",
    )
    return JSONResponse(
        status_code=status, content=_payload("Database temporarily unavailable", error=exc, extra=extra)
    )


@inject
async def data_error_handler(
    _req: Request,
    exc: DataError,
    db: Annotated[Database, Depends(Database, persist=True)],
):
    logger.error("Invalid data", exc_info=exc)
    status, extra = _map_with_dialect(
        db=db,
        exc=exc,
        default_status=400,
        default_reason="invalid_data",
    )
    return JSONResponse(status_code=status, content=_payload("Invalid data", error=exc, extra=extra))


@inject
async def programming_error_handler(
    _req: Request,
    exc: ProgrammingError,
    db: Annotated[Database, Depends(Database, persist=True)],
):
    logger.error("Database programming error", exc_info=exc)
    status, extra = _map_with_dialect(
        db=db,
        exc=exc,
        default_status=500,
        default_reason="db_programming_error",
    )
    return JSONResponse(status_code=status, content=_payload("Database programming error", error=exc, extra=extra))


@inject
async def dbapi_error_handler(
    _req: Request,
    exc: DBAPIError,
    db: Annotated[Database, Depends(Database, persist=True)],
):
    logger.error("Database error", exc_info=exc)
    status, extra = _map_with_dialect(
        db=db,
        exc=exc,
        default_status=503,
        default_reason="db_error",
    )
    return JSONResponse(status_code=status, content=_payload("Database error", error=exc, extra=extra))


async def no_result_handler(_req: Request, exc: NoResultFound):
    logger.error("Resource not found", exc_info=exc)
    return JSONResponse(
        status_code=404, content=_payload("Resource not found", error=exc, extra={"reason": "not_found"})
    )


async def multi_result_handler(_req: Request, exc: MultipleResultsFound):
    logger.error("Multiple resources matched", exc_info=exc)
    return JSONResponse(
        status_code=409, content=_payload("Multiple resources matched", error=exc, extra={"reason": "multiple_results"})
    )
