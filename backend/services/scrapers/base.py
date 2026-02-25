"""
Base web scraper with Selenium WebDriver management.

This module provides the base class for web scraping with:
- WebDriver initialization and cleanup
- Headless mode support
- Anti-bot bypass configurations
- Resource management
"""

import time
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base scraper class with WebDriver management.

    This class handles:
    - WebDriver initialization with proper options
    - Headless mode configuration
    - Anti-bot detection measures
    - Resource cleanup
    """

    def __init__(self, headless: bool = False):
        """Initialize the base scraper.

        Args:
            headless (bool): Whether to run browser in headless mode.
                Defaults to False.
        """
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self._wait: Optional[WebDriverWait] = None

    def init_webdriver(self) -> webdriver.Chrome:
        """Initialize the Selenium WebDriver with Chrome options.

        Sets up:
        - Headless mode if specified
        - Window size configuration
        - Anti-bot detection measures
        - User agent configuration

        Returns:
            webdriver.Chrome: Initialized Chrome WebDriver
        """
        if self.driver is not None:
            logger.warning("WebDriver already initialized")
            return self.driver

        options = Options()
        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')

        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script(
                """
                Object.defineProperty(
                    navigator, 'webdriver', {get: () => undefined}
                )
                """
            )

            if not self.headless:
                self.driver.set_window_size(1920, 1080)

            self._wait = WebDriverWait(self.driver, 10)

            logger.info(
                "WebDriver initialized successfully (headless=%s)",
                self.headless
            )
            return self.driver

        except WebDriverException as error:
            logger.error("Failed to initialize WebDriver: %s", error)
            raise

    def get_page(self, url: str, wait_time: float = 1.5) -> None:
        """Navigate to a URL and wait for page load.

        Args:
            url (str): URL to navigate to
            wait_time (float): Time to wait after page load in seconds
        """
        if self.driver is None:
            raise RuntimeError(
                "WebDriver not initialized. Call init_webdriver() first."
            )

        logger.info("Navigating to: %s", url)
        self.driver.get(url)
        time.sleep(wait_time)

    def get_page_source(self) -> str:
        """Get the current page source.

        Returns:
            str: HTML source of the current page
        """
        if self.driver is None:
            raise RuntimeError(
                "WebDriver not initialized. Call init_webdriver() first."
            )

        return self.driver.page_source

    def quit(self) -> None:
        """Close the WebDriver and cleanup resources."""
        if self.driver is not None:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except WebDriverException as error:
                logger.error("Error closing WebDriver: %s", error)
            finally:
                self.driver = None
                self._wait = None

    def __enter__(self):
        """Context manager entry."""
        self.init_webdriver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.quit()
