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