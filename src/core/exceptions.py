from fastapi           import HTTPException
from fastapi.responses import JSONResponse
from fastapi           import Request
from src.core.schemas  import ErrorResponse


class PhantomAPIException(HTTPException):
    def __init__(self, status_code: int, error: str, detail: str = None):
        super().__init__(status_code=status_code, detail=error)
        self.error  = error
        self.extra  = detail


class WAFBypassFailed(PhantomAPIException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=503,
            error="WAF bypass failed. The target site blocked the request.",
            detail=detail,
        )


class PageLoadTimeout(PhantomAPIException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=408,
            error="Page load timed out after all retry attempts.",
            detail=detail,
        )


class EmptyContentError(PhantomAPIException):
    def __init__(self):
        super().__init__(
            status_code=422,
            error="Extracted page content is empty after DOM cleaning.",
        )


class OpenAIAuthError(PhantomAPIException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error="OpenAI authentication failed. Verify your API key.",
        )


class OpenAIRateLimitError(PhantomAPIException):
    def __init__(self):
        super().__init__(
            status_code=429,
            error="OpenAI rate limit exceeded. Please retry later.",
        )


class OpenAIConnectionError(PhantomAPIException):
    def __init__(self):
        super().__init__(
            status_code=503,
            error="Could not connect to OpenAI API.",
        )


async def phantom_exception_handler(
    request: Request,
    exc:     PhantomAPIException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=exc.error,
            detail=exc.extra,
            code=exc.status_code,
        ).model_dump(),
    )


async def http_exception_handler(
    request: Request,
    exc:     HTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=str(exc.detail),
            code=exc.status_code,
        ).model_dump(),
    )


async def generic_exception_handler(
    request: Request,
    exc:     Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="An unexpected internal server error occurred.",
            detail=str(exc),
            code=500,
        ).model_dump(),
    )