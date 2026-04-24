import uvicorn
from contextlib        import asynccontextmanager
from fastapi           import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors    import RateLimitExceeded
from slowapi           import _rate_limit_exceeded_handler

from src.core.config         import settings
from src.core.exceptions     import (
    PhantomAPIException,
    phantom_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from src.api.routes          import router
from src.api.middleware       import request_logger_middleware
from src.utils.proxy_manager  import proxy_manager
from src.utils.rate_limiter   import limiter
from src.utils.logger         import setup_logger


logger = setup_logger("PhantomAPI.Main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info(f"  {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"  Environment : {settings.APP_ENV}")
    logger.info(f"  Host        : {settings.APP_HOST}:{settings.APP_PORT}")
    logger.info("=" * 60)

    proxy_manager.load()

    logger.info(f"  Proxy support : {'enabled' if proxy_manager.count > 0 else 'disabled'}")
    logger.info(f"  Rate limit    : {settings.RATE_LIMIT_PER_MINUTE} req/min")
    logger.info(f"  Max content   : {settings.MAX_CONTENT_CHARS} chars")
    logger.info("=" * 60)
    logger.info("  Engine is ready. Listening for requests.")
    logger.info("=" * 60)

    yield

    logger.info("PhantomAPI engine shutting down gracefully.")


app = FastAPI(
    title       = settings.APP_NAME,
    version     = settings.APP_VERSION,
    description = (
        "PhantomAPI — Stealth WAF-bypass scraping engine "
        "with AI-powered structured data extraction."
    ),
    docs_url    = "/docs",
    redoc_url   = "/redoc",
    lifespan    = lifespan,
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.middleware("http")(request_logger_middleware)

app.add_exception_handler(RateLimitExceeded,       _rate_limit_exceeded_handler)
app.add_exception_handler(PhantomAPIException,     phantom_exception_handler)
app.add_exception_handler(HTTPException,           http_exception_handler)
app.add_exception_handler(Exception,               generic_exception_handler)

app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host      = settings.APP_HOST,
        port      = settings.APP_PORT,
        reload    = False,
        workers   = 1,
        log_level = "warning",
    )