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