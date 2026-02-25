"""
CafeF financial report scraper.

This module provides functionality to scrape financial report data
from cafef.vn website, returning structured JSON data.
"""

import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.services.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CafeFScraper(BaseScraper):
    """Scraper for cafef.vn financial reports.

    This scraper extracts financial report metadata including:
    - Stock symbol and company name
    - Report name and time period
    - Document URLs
    """

    BASE_URL_TEMPLATE = (
        "https://cafef.vn/du-lieu/hose/{symbol}"
        "-bao-cao-tai-chinh.chn"
    )

    def __init__(self, headless: bool = False):
        """Initialize CafeF scraper.

        Args:
            headless (bool): Whether to run browser in headless mode
        """
        super().__init__(headless=headless)

    def scrape_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """Scrape financial report data for a given stock symbol.

        Args:
            symbol (str): Stock symbol to scrape (e.g., 'FPT')

        Returns:
            List[Dict[str, Any]]: List of report dictionaries with keys:
                - symbol: Stock symbol (lowercase)
                - company_name: Company name (lowercase)
                - report_time: Report period (e.g., 'Q3/2025')
                - report_name: Report name/type
                - report_url: URL to download the report

        Raises:
            RuntimeError: If WebDriver is not initialized
            ValueError: If no report data is found for the symbol
        """
        if self.driver is None:
            raise RuntimeError(
                "WebDriver not initialized. Call init_webdriver() first."
            )

        url = self.BASE_URL_TEMPLATE.format(symbol=symbol.lower())

        logger.info("Scraping data for symbol: %s from %s", symbol, url)

        self.get_page(url, wait_time=1.5)
        html = self.get_page_source()
        soup = BeautifulSoup(html, "lxml")

        company_name_tag = soup.find("h1", class_="title-content-name")
        company_name = company_name_tag.get_text(
            strip=True
        ).lower() if company_name_tag else None

        if not company_name:
            logger.warning(
                "Could not find company name for symbol: %s",
                symbol
            )

        report_table = soup.find(
            "tbody", class_="render_dataBCTC"
        )

        if not report_table:
            logger.error("No report table found for symbol: %s", symbol)
            raise ValueError(f"No report data found for symbol: {symbol}")

        rows = report_table.find_all("tr")
        reports = []

        for row in rows:
            try:
                report_name_tag = row.find("td", class_="BCTC_body_type")
                report_name = report_name_tag.get_text(
                    strip=True
                ).lower() if report_name_tag else None

                report_time_tag = row.find("td", class_="BCTC_body_dateTime")
                report_time = report_time_tag.get_text(
                    strip=True
                ).lower() if report_time_tag else None

                download_tag = row.find("td", class_="BCTC_body_download")
                link_tag = download_tag.find("a") if download_tag else None
                report_url = (
                    link_tag["href"]
                    if link_tag and "href" in link_tag.attrs
                    else None
                )

                if isinstance(report_url, str) and report_url.startswith("//"):
                    report_url = f"https:{report_url}"

                report = {
                    "symbol": symbol.lower(),
                    "company_name": company_name,
                    "report_time": report_time,
                    "report_name": report_name,
                    "report_url": report_url
                }

                reports.append(report)

            except (AttributeError, KeyError, TypeError) as error:
                logger.warning(
                    "Error parsing row for symbol %s: %s", symbol, error
                )
                continue

        logger.info("Scraped %d reports for symbol: %s", len(reports), symbol)

        return reports

    def scrape_multiple_symbols(
        self, symbols: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape financial report data for multiple stock symbols.

        Args:
            symbols (List[str]): List of stock symbols to scrape

        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary mapping symbols to
            their reports
        """
        results = {}

        for symbol in symbols:
            try:
                reports = self.scrape_symbol(symbol)
                results[symbol] = reports
            except (RuntimeError, ValueError) as e:
                logger.error("Failed to scrape symbol %s: %s", symbol, e)
                results[symbol] = []

        return results
