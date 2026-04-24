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