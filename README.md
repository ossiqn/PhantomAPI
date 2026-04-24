Önce tam proje ağacını vereyim, sonra her dosyayı sırayla yazacağım.

```
PhantomAPI/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── middleware.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── schemas.py
│   │   └── exceptions.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── scraper.py
│   │   └── ai_parser.py
│   └── utils/
│       ├── __init__.py
│       ├── proxy_manager.py
│       ├── rate_limiter.py
│       └── logger.py
```

---

**`requirements.txt`**

```txt
fastapi==0.111.0
uvicorn[standard]==0.30.1
undetected-chromedriver==3.5.5
selenium==4.21.0
beautifulsoup4==4.12.3
lxml==5.2.2
openai==1.30.1
pydantic==2.7.1
pydantic-settings==2.3.0
python-dotenv==1.0.1
slowapi==0.1.9
tenacity==8.3.0
httpx==0.27.0
colorlog==6.8.2
```

---

**`.env.example`**

```env
APP_HOST=0.0.0.0
APP_PORT=8000
APP_ENV=production
APP_DEBUG=false

PAGE_LOAD_TIMEOUT=30
RETRY_ATTEMPTS=3
RETRY_DELAY=2
MAX_CONTENT_CHARS=12000
PROXY_FILE_PATH=proxies.txt

RATE_LIMIT_PER_MINUTE=30
```

---

**`.gitignore`**

```gitignore
__pycache__/
*.py[cod]
*.pyo
.env
*.log
proxies.txt
.venv/
venv/
dist/
build/
*.egg-info/
.DS_Store
Thumbs.db
.idea/
.vscode/
chromedriver
chromedriver.exe
*.tmp
```

---

**`src/utils/logger.py`**

```python
import logging
import sys
from colorlog import ColoredFormatter


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    formatter = ColoredFormatter(
        fmt=(
            "%(log_color)s%(asctime)s%(reset)s "
            "%(blue)s[%(name)s]%(reset)s "
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(white)s%(message)s%(reset)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "bold_red",
        },
        reset=True,
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
```

---

**`src/core/config.py`**

```python
from pydantic_settings import BaseSettings
from functools         import lru_cache


class AppSettings(BaseSettings):
    APP_NAME:    str = "PhantomAPI"
    APP_VERSION: str = "2.0.0"
    APP_HOST:    str = "0.0.0.0"
    APP_PORT:    int = 8000
    APP_ENV:     str = "production"
    APP_DEBUG:   bool = False

    PAGE_LOAD_TIMEOUT: int = 30
    RETRY_ATTEMPTS:    int = 3
    RETRY_DELAY:       int = 2
    MAX_CONTENT_CHARS: int = 12000
    PROXY_FILE_PATH:   str = "proxies.txt"

    RATE_LIMIT_PER_MINUTE: int = 30

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


settings = get_settings()
```

---

**`src/core/schemas.py`**

```python
from pydantic import BaseModel, HttpUrl, field_validator
from typing   import Optional, Any


class ExtractionRequest(BaseModel):
    url:             HttpUrl
    prompt:          str
    wait_for_selector: Optional[str] = None
    javascript:      Optional[str]   = None

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Prompt field cannot be empty.")
        return stripped

    @field_validator("javascript")
    @classmethod
    def javascript_length_guard(cls, value: Optional[str]) -> Optional[str]:
        if value and len(value) > 2000:
            raise ValueError("Custom JavaScript cannot exceed 2000 characters.")
        return value


class ExtractionResponse(BaseModel):
    success:        bool
    url:            str
    extracted_data: dict[str, Any]
    tokens_used:    Optional[int]  = None
    proxy_used:     Optional[str]  = None
    elapsed_ms:     Optional[float] = None


class HealthResponse(BaseModel):
    status:      str
    service:     str
    version:     str
    environment: str
    proxy_count: int


class ErrorResponse(BaseModel):
    success: bool        = False
    error:   str
    detail:  Optional[str] = None
    code:    Optional[int]  = None
```

---

**`src/core/exceptions.py`**

```python
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
```

---

**`src/utils/proxy_manager.py`**

```python
import os
import random
from typing        import Optional
from src.core.config  import settings
from src.utils.logger import setup_logger


logger = setup_logger("PhantomAPI.ProxyManager")


class ProxyManager:

    def __init__(self) -> None:
        self._proxies: list[str] = []
        self._loaded:  bool      = False
        self._current: Optional[str] = None

    def load(self) -> None:
        path = settings.PROXY_FILE_PATH

        if not os.path.exists(path):
            logger.warning(
                f"Proxy file '{path}' not found. Running without proxy support."
            )
            self._proxies = []
            self._loaded  = True
            return

        with open(path, "r", encoding="utf-8") as file:
            lines = [
                line.strip()
                for line in file
                if line.strip() and not line.startswith("#")
            ]

        self._proxies = lines
        self._loaded  = True

        logger.info(f"{len(self._proxies)} proxies loaded from '{path}'.")

    def get_random(self) -> Optional[str]:
        if not self._loaded:
            self.load()

        if not self._proxies:
            return None

        self._current = random.choice(self._proxies)
        logger.info(f"Proxy selected -> {self._current}")
        return self._current

    def remove_bad_proxy(self, proxy: str) -> None:
        if proxy in self._proxies:
            self._proxies.remove(proxy)
            logger.warning(f"Bad proxy removed: {proxy} | Remaining: {len(self._proxies)}")

    def reload(self) -> None:
        self._loaded  = False
        self._proxies = []
        self.load()

    @property
    def count(self) -> int:
        return len(self._proxies)

    @property
    def current(self) -> Optional[str]:
        return self._current


proxy_manager = ProxyManager()
```

---

**`src/utils/rate_limiter.py`**

```python
from slowapi         import Limiter
from slowapi.util    import get_remote_address
from src.core.config import settings


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)
```

---

**`src/services/scraper.py`**

```python
import time
import random
from typing          import Optional
from tenacity        import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support    import expected_conditions as EC
from selenium.webdriver.common.by  import By
from selenium.common.exceptions    import TimeoutException, WebDriverException
from bs4                           import BeautifulSoup

from src.core.config         import settings
from src.core.exceptions     import WAFBypassFailed, PageLoadTimeout, EmptyContentError
from src.utils.proxy_manager import proxy_manager
from src.utils.logger        import setup_logger


logger = setup_logger("PhantomAPI.Scraper")


_STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver',       { get: () => undefined });
    Object.defineProperty(navigator, 'plugins',         { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages',       { get: () => ['en-US', 'en'] });
    Object.defineProperty(navigator, 'platform',        { get: () => 'Win32' });
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    Object.defineProperty(navigator, 'deviceMemory',    { get: () => 8 });
    Object.defineProperty(screen,    'width',           { get: () => 1920 });
    Object.defineProperty(screen,    'height',          { get: () => 1080 });
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi:        function() {},
        app:        {}
    };
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);
"""


class ScraperService:

    def _build_options(self, proxy: Optional[str]) -> uc.ChromeOptions:
        options = uc.ChromeOptions()

        flags = [
            "--headless=new",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-extensions",
            "--disable-popup-blocking",
            "--disable-notifications",
            "--disable-default-apps",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-translate",
            "--ignore-certificate-errors",
            "--window-size=1920,1080",
            "--start-maximized",
            "--hide-scrollbars",
            "--mute-audio",
            "--no-first-run",
            "--no-default-browser-check",
            "--lang=en-US,en",
            (
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        ]

        for flag in flags:
            options.add_argument(flag)

        if proxy:
            options.add_argument(f"--proxy-server={proxy}")

        return options

    def _create_driver(self, proxy: Optional[str]) -> uc.Chrome:
        options = self._build_options(proxy=proxy)
        driver  = uc.Chrome(options=options, use_subprocess=True)

        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": _STEALTH_SCRIPT},
        )

        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {
                "userAgent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "acceptLanguage": "en-US,en;q=0.9",
                "platform":       "Win32",
            },
        )

        driver.set_page_load_timeout(settings.PAGE_LOAD_TIMEOUT)
        return driver

    def _clean_html(self, raw_html: str) -> str:
        soup = BeautifulSoup(raw_html, "lxml")

        for tag in soup(
            ["script", "style", "svg", "noscript",
             "iframe", "meta", "link", "head"]
        ):
            tag.decompose()

        for tag in soup.find_all(True):
            tag.attrs = {}

        text  = soup.get_text(separator="\n", strip=True)
        lines = [line for line in text.splitlines() if line.strip()]
        clean = "\n".join(lines)

        if len(clean) > settings.MAX_CONTENT_CHARS:
            logger.warning(
                f"Content truncated: {len(clean)} -> {settings.MAX_CONTENT_CHARS} chars."
            )
            clean = clean[: settings.MAX_CONTENT_CHARS]

        return clean

    def _execute_custom_js(self, driver: uc.Chrome, script: str) -> None:
        try:
            driver.execute_script(script)
            logger.info("Custom JavaScript executed successfully.")
        except Exception as exc:
            logger.warning(f"Custom JavaScript execution failed: {exc}")

    def _wait_for_element(
        self,
        driver:   uc.Chrome,
        selector: str,
    ) -> None:
        try:
            WebDriverWait(driver, settings.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            logger.info(f"Element found -> '{selector}'")
        except TimeoutException:
            logger.warning(f"Element not found within timeout -> '{selector}'")

    def fetch(
        self,
        url:              str,
        wait_for_selector: Optional[str] = None,
        custom_js:        Optional[str]  = None,
    ) -> tuple[str, Optional[str]]:
        proxy  = proxy_manager.get_random()
        driver = None

        for attempt in range(1, settings.RETRY_ATTEMPTS + 1):
            try:
                logger.info(
                    f"[Attempt {attempt}/{settings.RETRY_ATTEMPTS}] "
                    f"Fetching -> {url} "
                    f"| Proxy: {proxy or 'None'}"
                )

                driver = self._create_driver(proxy=proxy)
                driver.get(url)

                WebDriverWait(driver, settings.PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                if wait_for_selector:
                    self._wait_for_element(driver, wait_for_selector)

                if custom_js:
                    self._execute_custom_js(driver, custom_js)

                time.sleep(random.uniform(2.0, 4.5))

                raw_html   = driver.page_source
                clean_text = self._clean_html(raw_html)

                if not clean_text.strip():
                    raise EmptyContentError()

                logger.info(
                    f"Fetch successful on attempt {attempt}. "
                    f"Content size: {len(clean_text)} chars."
                )

                return clean_text, proxy

            except EmptyContentError:
                raise

            except TimeoutException:
                logger.warning(f"Attempt {attempt} timed out.")

                if proxy:
                    proxy_manager.remove_bad_proxy(proxy)
                    proxy = proxy_manager.get_random()

                if attempt == settings.RETRY_ATTEMPTS:
                    raise PageLoadTimeout(detail=f"URL: {url}")

            except WebDriverException as exc:
                logger.error(f"WebDriver error on attempt {attempt}: {exc.msg}")

                if proxy:
                    proxy_manager.remove_bad_proxy(proxy)
                    proxy = proxy_manager.get_random()

                if attempt == settings.RETRY_ATTEMPTS:
                    raise WAFBypassFailed(detail=exc.msg)

            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = None

            backoff = settings.RETRY_DELAY * (2 ** (attempt - 1))
            jitter  = random.uniform(0.5, 1.5)
            sleep   = backoff + jitter

            logger.info(f"Retrying in {sleep:.1f}s...")
            time.sleep(sleep)

        raise WAFBypassFailed(detail=f"All {settings.RETRY_ATTEMPTS} attempts exhausted.")


scraper_service = ScraperService()
```

---

**`src/services/ai_parser.py`**

```python
import json
from typing import Any

from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError

from src.core.exceptions import (
    OpenAIAuthError,
    OpenAIRateLimitError,
    OpenAIConnectionError,
    PhantomAPIException,
)
from src.utils.logger import setup_logger


logger = setup_logger("PhantomAPI.AIParser")


_SYSTEM_PROMPT = """
You are PhantomAPI's precision data extraction engine.

Rules you must follow without exception:
1. Read the PAGE CONTENT and the EXTRACTION PROMPT carefully.
2. Extract ONLY the data the prompt requests.
3. Return the result as a single, valid JSON object.
4. NEVER include markdown, code fences, explanations, or extra text.
5. If the requested data is not found, return: {"result": null, "reason": "Data not found in page content."}
6. Structure the JSON logically based on the extraction prompt.
"""


class AIParserService:

    def _build_messages(self, content: str, prompt: str) -> list[dict[str, str]]:
        user_message = (
            f"EXTRACTION PROMPT:\n{prompt}\n\n"
            f"PAGE CONTENT:\n{content}"
        )

        return [
            {"role": "system", "content": _SYSTEM_PROMPT.strip()},
            {"role": "user",   "content": user_message},
        ]

    def parse(
        self,
        content: str,
        prompt:  str,
        api_key: str,
    ) -> tuple[dict[str, Any], int]:
        client = OpenAI(api_key=api_key)

        try:
            logger.info("Sending content to OpenAI gpt-4o for extraction...")

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=self._build_messages(content, prompt),
                temperature=0.0,
                response_format={"type": "json_object"},
            )

        except AuthenticationError:
            raise OpenAIAuthError()

        except RateLimitError:
            raise OpenAIRateLimitError()

        except APIConnectionError:
            raise OpenAIConnectionError()

        except Exception as exc:
            raise PhantomAPIException(
                status_code=500,
                error="Unexpected OpenAI API error.",
                detail=str(exc),
            )

        raw_output  = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        try:
            extracted = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            logger.error(f"OpenAI returned invalid JSON: {exc}")
            raise PhantomAPIException(
                status_code=500,
                error="AI model returned malformed JSON.",
                detail="Try rephrasing your extraction prompt.",
            )

        logger.info(
            f"Extraction complete. "
            f"Tokens used: {tokens_used} | "
            f"Keys returned: {list(extracted.keys())}"
        )

        return extracted, tokens_used


ai_parser_service = AIParserService()
```

---

**`src/api/middleware.py`**

```python
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
```

---

**`src/api/routes.py`**

```python
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
```

---

**`main.py`**

```python
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
```

---

**`README.md`**

````markdown
<div align="center">
  <h1>👻 PhantomAPI</h1>
  <p>
    <b>Stealth WAF-bypass scraping engine with AI-powered structured data extraction.</b>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python"/>
    <img src="https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi"/>
    <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai"/>
    <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square"/>
  </p>
</div>

---

## What is PhantomAPI?

PhantomAPI is a production-grade REST API framework that turns any website into a
structured data source — even if that site has no public API and is protected by
Cloudflare, Datadome, or similar WAF layers.

**Flow:**
```
POST /api/v1/extract
        │
        ▼
Stealth Chrome (undetected-chromedriver)
  + Proxy rotation
  + Fingerprint spoofing
        │
        ▼
BeautifulSoup DOM cleaner
  (scripts / styles / svg stripped)
        │
        ▼
OpenAI GPT-4o
  (json_object mode)
        │
        ▼
Clean JSON response
```

---

## Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| API         | FastAPI + Uvicorn                 |
| Scraping    | undetected-chromedriver + Selenium|
| DOM Parsing | BeautifulSoup4 + lxml             |
| AI Engine   | OpenAI GPT-4o                     |
| Validation  | Pydantic v2                       |
| Rate Limit  | SlowAPI                           |
| Retries     | Tenacity                          |
| Logging     | colorlog                          |

---

## Setup

```bash
git clone https://github.com/yourname/PhantomAPI.git
cd PhantomAPI
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

---

## Usage

```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
     -H "Content-Type: application/json" \
     -H "X-OpenAI-Key: sk-..." \
     -d '{
           "url": "https://target-site.com/products",
           "prompt": "Extract all product names and prices as a JSON array."
         }'
```

### Optional fields

| Field               | Type   | Description                                      |
|---------------------|--------|--------------------------------------------------|
| `wait_for_selector` | string | CSS selector to wait for before capturing DOM    |
| `javascript`        | string | Custom JS to execute after page load (max 2000c) |

### Response

```json
{
  "success": true,
  "url": "https://target-site.com/products",
  "extracted_data": {
    "products": [
      { "name": "Product A", "price": "$19.99" },
      { "name": "Product B", "price": "$34.99" }
    ]
  },
  "tokens_used": 812,
  "proxy_used": "http://1.2.3.4:8080",
  "elapsed_ms": 7430.21
}
```

---

## Proxy Support

Create a `proxies.txt` file in the project root:

```
http://user:pass@1.2.3.4:8080
socks5://9.10.11.12:1080
http://5.6.7.8:3128
```

Lines starting with `#` are ignored.
Bad proxies (timeout/WebDriver failure) are auto-removed from rotation.

---

## Endpoints

| Method | Path               | Description            |
|--------|--------------------|------------------------|
| POST   | `/api/v1/extract`  | Run extraction         |
| GET    | `/api/v1/health`   | Engine health check    |
| GET    | `/docs`            | Swagger UI             |
| GET    | `/redoc`           | ReDoc UI               |

---

## Environment Variables

| Variable               | Default        | Description                   |
|------------------------|----------------|-------------------------------|
| `APP_HOST`             | `0.0.0.0`      | Server host                   |
| `APP_PORT`             | `8000`         | Server port                   |
| `APP_ENV`              | `production`   | Environment label             |
| `PAGE_LOAD_TIMEOUT`    | `30`           | Seconds before timeout        |
| `RETRY_ATTEMPTS`       | `3`            | Max browser retry count       |
| `RETRY_DELAY`          | `2`            | Base delay between retries    |
| `MAX_CONTENT_CHARS`    | `12000`        | Max chars sent to OpenAI      |
| `PROXY_FILE_PATH`      | `proxies.txt`  | Path to proxy list            |
| `RATE_LIMIT_PER_MINUTE`| `30`           | Max requests per minute / IP  |

---

## License

MIT
````
