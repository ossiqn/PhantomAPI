import time
import uuid
from fastapi           import Request
from fastapi.responses import Response
from src.utils.logger  import setup_logger


logger = setup_logger("PhantomAPI.Middleware")


async def request_logger_middleware(request: Request, call_next) -> Response:
    request_id = str(uuid.uuid4())[:8]
    start_time = time.perf_counter()

    logger.info(
        f"[{request_id}] Incoming -> {request.method} {request.url.path} "
        f"| Client: {request.client.host}"
    )

    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        f"[{request_id}] Completed -> {response.status_code} "
        f"| {elapsed_ms:.2f}ms"
    )

    response.headers["X-Request-ID"]    = request_id
    response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"
    response.headers["X-Powered-By"]    = "PhantomAPI"

    return response