from fastapi import FastAPI
from sqlalchemy.exc import (
    DataError,
    DBAPIError,
    IntegrityError,
    MultipleResultsFound,
    NoResultFound,
    OperationalError,
    ProgrammingError,
)

from .handlers import (
    data_error_handler,
    dbapi_error_handler,
    integrity_error_handler,
    multi_result_handler,
    no_result_handler,
    operational_error_handler,
    programming_error_handler,
)


def register_database_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(OperationalError, operational_error_handler)
    app.add_exception_handler(DataError, data_error_handler)
    app.add_exception_handler(ProgrammingError, programming_error_handler)
    app.add_exception_handler(DBAPIError, dbapi_error_handler)
    app.add_exception_handler(NoResultFound, no_result_handler)
    app.add_exception_handler(MultipleResultsFound, multi_result_handler)
