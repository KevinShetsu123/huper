"""Scraper service package."""

from backend.services.scrapers.base import BaseScraper
from backend.services.scrapers.cafef import CafeFScraper

__all__ = [
    "BaseScraper",
    "CafeFScraper"
]
