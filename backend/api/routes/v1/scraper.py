"""
Scraper API endpoints.

This module provides REST API endpoints for scraping financial reports:
- Single symbol scraping
- Bulk symbol scraping
- Integration with database storage
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.session import Session
from pydantic import ValidationError
from backend.database import get_session
from backend.database.repositories import ReportRepository
from backend.schemas import (
    ScraperRequest,
    ScraperResponse,
    BulkScraperRequest,
    BulkScraperResponse,
    FinancialReportCreate,
    FinancialReportResponse,
)
from backend.services.scrapers import CafeFScraper
from backend.services.processors import process_reports


logger = logging.getLogger(__name__)

router = APIRouter(tags=["scraper"])


@router.post("/scrape", response_model=ScraperResponse)
async def scrape_symbol(
    request: ScraperRequest, db: Session = Depends(get_session)
) -> ScraperResponse:
    """Scrape financial reports for a single stock symbol.

    This endpoint:
    1. Scrapes report metadata from CafeF website
    2. Processes and validates the data
    3. Saves to database (always enabled)
    4. Returns the scraped reports

    Args:
        request (ScraperRequest): Scraping configuration
        db (Session): Database session

    Returns:
        ScraperResponse: Scraping results with statistics

    Raises:
        HTTPException: If scraping fails or validation errors occur
    """
    logger.info("Scraping symbol: %s", request.symbol)

    scraper = None
    try:
        scraper = CafeFScraper(headless=request.headless)
        scraper.init_webdriver()
        raw_reports = scraper.scrape_symbol(request.symbol)

        if not raw_reports:
            return ScraperResponse(
                success=True,
                message=f"No reports found for symbol: {request.symbol}",
                symbol=request.symbol,
                reports_count=0,
            )

        processed_reports = process_reports(raw_reports)
        if not processed_reports:
            return ScraperResponse(
                success=True,
                message=f"""
                    All reports filtered out for symbol: {request.symbol}
                """,
                symbol=request.symbol,
                reports_count=0,
            )

        validated_reports = []
        validation_errors = []
        for report in processed_reports:
            try:
                validated = FinancialReportCreate(**report)
                validated_reports.append(validated)
            except ValidationError as error:
                logger.warning("Validation error for report: %s", error)
                validation_errors.append(str(error))

        if not validated_reports:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "All reports failed validation",
                    "errors": validation_errors,
                },
            )

        created_count = 0
        updated_count = 0
        saved_reports = []
        repository = ReportRepository(db)

        for validated_report in validated_reports:
            report_dict = validated_report.model_dump()
            saved_report, created = repository.upsert(report_dict)
            if created:
                created_count += 1
            else:
                updated_count += 1

            saved_reports.append(
                FinancialReportResponse.model_validate(
                    saved_report
                )
            )

        return ScraperResponse(
            success=True,
            message=f"""
            Successfully scraped {len(validated_reports)}
            reports for {request.symbol}
            """,
            symbol=request.symbol,
            reports_count=len(validated_reports),
            created_count=created_count,
            updated_count=updated_count,
            reports=saved_reports,
        )

    except ValueError as error:
        logger.error("Scraping error for %s: %s", request.symbol, error)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to scrape {request.symbol}: {str(error)}",
        ) from error

    except (RuntimeError, OSError, IOError) as error:
        logger.error(
            "Unexpected error scraping %s: %s",
            request.symbol, error, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(error)}",
        ) from error

    finally:
        if scraper:
            scraper.quit()


@router.post("/scrape-bulk", response_model=BulkScraperResponse)
async def scrape_bulk(
    request: BulkScraperRequest, db: Session = Depends(get_session)
) -> BulkScraperResponse:
    """Scrape financial reports for multiple stock symbols.

    This endpoint processes multiple symbols sequentially,
    providing individual results for each symbol.

    Args:
        request (BulkScraperRequest): Bulk scraping configuration
        db (Session): Database session

    Returns:
        BulkScraperResponse: Aggregated results for all symbols
    """
    logger.info("Bulk scraping %d symbols", len(request.symbols))

    results: List[ScraperResponse] = []
    total_reports = 0
    total_created = 0
    total_updated = 0
    successful_count = 0
    failed_count = 0

    for symbol in request.symbols:
        try:
            single_request = ScraperRequest(
                symbol=symbol, headless=request.headless
            )
            result = await scrape_symbol(single_request, db)
            results.append(result)

            if result.success:
                successful_count += 1
                total_reports += result.reports_count
                total_created += result.created_count
                total_updated += result.updated_count
            else:
                failed_count += 1

        except HTTPException as error:
            logger.warning("Failed to scrape %s: %s", symbol, error.detail)
            failed_count += 1
            results.append(
                ScraperResponse(
                    success=False,
                    message=str(error.detail),
                    symbol=symbol,
                    reports_count=0,
                )
            )

        except (ValueError, RuntimeError, OSError, IOError) as error:
            logger.error("Unexpected error scraping %s: %s", symbol, error)
            failed_count += 1

            results.append(
                ScraperResponse(
                    success=False,
                    message=f"Unexpected error: {str(error)}",
                    symbol=symbol,
                    reports_count=0,
                )
            )

    return BulkScraperResponse(
        success=failed_count == 0,
        message=f"""
        Processed {len(request.symbols)} symbols: {successful_count}
        succeeded, {failed_count} failed
        """,
        total_symbols=len(request.symbols),
        successful_symbols=successful_count,
        failed_symbols=failed_count,
        total_reports=total_reports,
        total_created=total_created,
        total_updated=total_updated,
        results=results,
    )
