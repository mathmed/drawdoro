from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.errors.domain_errors import (
    ConflictError,
    DomainError,
    ForbiddenError,
    InvalidInputError,
    NotFoundError,
    PayloadTooLargeError,
    ServiceUnavailableError,
    UnauthorizedError,
)

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
    InvalidInputError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    PayloadTooLargeError: status.HTTP_413_CONTENT_TOO_LARGE,
    ServiceUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


async def domain_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)  # nosec B101 - only registered for DomainError
    status_code = next(
        (code for error, code in STATUS_BY_ERROR.items() if isinstance(exc, error)),
        status.HTTP_400_BAD_REQUEST,
    )
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
