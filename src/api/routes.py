import asyncio
import time
from fastapi           import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from src.core.schemas        import (
    ExtractionRequest,
    ExtractionResponse,
    HealthResponse,
)
from src.core.exceptions     import PhantomAPIException
from src.services.scraper    import scraper_service
from src.services.ai_parser  import ai_parser_service
from src.utils.proxy_manager import proxy_manager
from src.utils.rate_limiter  import limiter
from src.core.config         import settings
from src.utils.logger        import setup_logger


logger = setup_logger("PhantomAPI.Routes")
router = APIRouter()


@router.post("/extract", response_model=ExtractionResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def extract(
    request:      Request,
    body:         ExtractionRequest,
    x_openai_key: str = Header(..., alias="X-OpenAI-Key"),
) -> ExtractionResponse:
    key = x_openai_key.strip()

    if not key or not key.startswith("sk-"):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing OpenAI API key in X-OpenAI-Key header.",
        )

    target_url = str(body.url)
    start_time = time.perf_counter()

    logger.info(f"New extraction request -> {target_url}")

    loop = asyncio.get_event_loop()

    clean_text, proxy_used = await loop.run_in_executor(
        None,
        lambda: scraper_service.fetch(
            url=target_url,
            wait_for_selector=body.wait_for_selector,
            custom_js=body.javascript,
        ),
    )

    extracted_data, tokens_used = await loop.run_in_executor(
        None,
        lambda: ai_parser_service.parse(
            content=clean_text,
            prompt=body.prompt,
            api_key=key,
        ),
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        f"Request fulfilled -> {target_url} "
        f"| Elapsed: {elapsed_ms:.0f}ms "
        f"| Tokens: {tokens_used}"
    )

    return ExtractionResponse(
        success=True,
        url=target_url,
        extracted_data=extracted_data,
        tokens_used=tokens_used,
        proxy_used=proxy_used,
        elapsed_ms=round(elapsed_ms, 2),
    )


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="operational",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        proxy_count=proxy_manager.count,
    )