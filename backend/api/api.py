"""
Central API Router.
"""

from fastapi import APIRouter
from backend.api.routes.v1 import scraper, financial

api_router = APIRouter()

api_router.include_router(
    scraper.router,
    prefix="/scraper",
    tags=["Scraper"],
)

api_router.include_router(
    financial.router,
    prefix="/financial",
    tags=["Financial Reports"],
)
