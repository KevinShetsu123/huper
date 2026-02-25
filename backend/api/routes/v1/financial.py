"""
Financial data API endpoints.

This module provides REST API endpoints for querying financial report data
that has been scraped and stored in the database.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm.session import Session
from backend.database import get_session
from backend.database.repositories import (
    ReportRepository,
    FinancialDataCoordinator,
    BalanceSheetItemRepository,
    IncomeStatementItemRepository,
    CashFlowItemRepository
)
from backend.schemas import (
    FinancialReportResponse,
    FinancialReportCreate,
    BalanceSheetItemCreate,
    IncomeStatementItemCreate,
    CashFlowItemCreate,
    FinancialStatementsResponse,
    BalanceSheetItemResponse,
    IncomeStatementItemResponse,
    CashFlowItemResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["financial"])


@router.get("/reports", response_model=List[FinancialReportResponse])
async def get_reports(
    symbol: Optional[str] = Query(
        None, description="Filter by stock symbol"
    ),
    report_type: Optional[str] = Query(
        None, description="Filter by report type (annual/quarterly)"
    ),
    report_year: Optional[int] = Query(
        None, description="Filter by report year"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of results"
    ),
    offset: int = Query(
        0, ge=0, description="Number of results to skip"
    ),
    db: Session = Depends(get_session)
) -> List[FinancialReportResponse]:
    """Get financial reports with optional filtering and pagination.

    Args:
        symbol: Filter by stock symbol
        report_type: Filter by report type (annual/quarterly)
        report_year: Filter by report year
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session

    Returns:
        List of financial reports
    """
    repository = ReportRepository(db)

    if symbol:
        reports = repository.get_by_symbol(symbol)
    else:
        reports = repository.get_all(limit=limit, offset=offset)

    if report_type:
        reports = [
            r for r in reports
            if getattr(r, 'report_type', None) == report_type
        ]

    if report_year:
        reports = [
            r for r in reports
            if getattr(r, 'report_year', None) == report_year
        ]

    return [FinancialReportResponse.model_validate(r) for r in reports]


@router.get("/reports/{report_id}", response_model=FinancialReportResponse)
async def get_report_by_id(
    report_id: int,
    db: Session = Depends(get_session)
) -> FinancialReportResponse:
    """Get a specific financial report by ID.

    Args:
        report_id: Report ID
        db: Database session

    Returns:
        Financial report

    Raises:
        HTTPException: If report not found
    """
    repository = ReportRepository(db)
    report = repository.get_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    return FinancialReportResponse.model_validate(report)


@router.get(
    "/reports/symbol/{symbol}", response_model=List[FinancialReportResponse]
)
async def get_reports_by_symbol(
    symbol: str,
    db: Session = Depends(get_session)
) -> List[FinancialReportResponse]:
    """Get all financial reports for a specific stock symbol.

    Args:
        symbol: Stock symbol
        db: Database session

    Returns:
        List of financial reports for the symbol
    """
    repository = ReportRepository(db)
    reports = repository.get_by_symbol(symbol)

    return [FinancialReportResponse.model_validate(r) for r in reports]


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_session)
) -> dict:
    """Delete a financial report by ID.

    Args:
        report_id: Report ID
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If report not found
    """
    repository = ReportRepository(db)
    deleted = repository.delete(report_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )

    return {"message": f"Report {report_id} deleted successfully"}


@router.delete("/reports/symbol/{symbol}")
async def delete_reports_by_symbol(
    symbol: str,
    db: Session = Depends(get_session)
) -> dict:
    """Delete all financial reports for a specific symbol.

    Args:
        symbol: Stock symbol
        db: Database session

    Returns:
        Success message with count of deleted reports
    """
    repository = ReportRepository(db)
    count = repository.delete_by_symbol(symbol)

    return {
        "message": f"Deleted {count} reports for symbol {symbol}",
        "deleted_count": count
    }


@router.get("/stats")
async def get_stats(db: Session = Depends(get_session)) -> dict:
    """Get statistics about the financial reports database.

    Args:
        db: Database session

    Returns:
        Statistics dictionary
    """
    repository = ReportRepository(db)
    total_reports = repository.count()

    return {
        "total_reports": total_reports,
        "database": "operational"
    }


@router.post(
    "/complete-data",
    response_model=FinancialStatementsResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_complete_financial_data(
    report: FinancialReportCreate,
    balance_sheet_items: List[BalanceSheetItemCreate],
    income_statement_items: List[IncomeStatementItemCreate],
    cash_flow_items: List[CashFlowItemCreate],
    db: Session = Depends(get_session)
) -> FinancialStatementsResponse:
    """Add complete financial data (report + all items) to database.

    This endpoint creates a financial report and all associated items
    (balance sheet, income statement, cash flow) in a single transaction.

    Args:
        report: Financial report data
        balance_sheet_items: List of balance sheet items
        income_statement_items: List of income statement items
        cash_flow_items: List of cash flow items
        db: Database session

    Returns:
        Response with created report and item counts

    Raises:
        HTTPException: If creation fails
    """
    try:
        repository = FinancialDataCoordinator(db)

        report_data = report.model_dump()
        balance_data = [
            item.model_dump(exclude={'report_id'})
            for item in balance_sheet_items
        ]
        income_data = [
            item.model_dump(exclude={'report_id'})
            for item in income_statement_items
        ]
        cash_data = [
            item.model_dump(exclude={'report_id'})
            for item in cash_flow_items
        ]

        result = repository.add_complete_data(
            report_data=report_data,
            balance_sheet_items=balance_data,
            income_statement_items=income_data,
            cash_flow_items=cash_data
        )

        return FinancialStatementsResponse(
            report=result['report'],
            balance_sheet_items_count=result['balance_sheet_items_count'],
            income_statement_items_count=result[
                'income_statement_items_count'
            ],
            cash_flow_items_count=result['cash_flow_items_count'],
            message=f"""
                Successfully created financial report for {
                    report.symbol
                } with:
                - {
                    result['balance_sheet_items_count']
                } balance sheet items
                - {
                    result['income_statement_items_count']
                } income statement items
                - {result['cash_flow_items_count']} cash flow items
            """
        )

    except Exception as e:
        logger.error("Failed to add complete financial data: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add financial data: {str(e)}"
        ) from e


@router.get(
    "/reports/{report_id}/balance-sheet",
    response_model=List[BalanceSheetItemResponse]
)
async def get_balance_sheet_items(
    report_id: int,
    db: Session = Depends(get_session)
) -> List[BalanceSheetItemResponse]:
    """Get balance sheet items for a report.

    Args:
        report_id: Report ID
        db: Database session

    Returns:
        List of balance sheet items
    """
    repository = BalanceSheetItemRepository(db)
    items = repository.get_by_report_id(report_id)
    return [BalanceSheetItemResponse.model_validate(item) for item in items]


@router.get(
    "/reports/{report_id}/income-statement",
    response_model=List[IncomeStatementItemResponse]
)
async def get_income_statement_items(
    report_id: int,
    db: Session = Depends(get_session)
) -> List[IncomeStatementItemResponse]:
    """Get income statement items for a report.

    Args:
        report_id: Report ID
        db: Database session

    Returns:
        List of income statement items
    """
    repository = IncomeStatementItemRepository(db)
    items = repository.get_by_report_id(report_id)
    return [IncomeStatementItemResponse.model_validate(item) for item in items]


@router.get(
    "/reports/{report_id}/cash-flow",
    response_model=List[CashFlowItemResponse]
)
async def get_cash_flow_items(
    report_id: int,
    db: Session = Depends(get_session)
) -> List[CashFlowItemResponse]:
    """Get cash flow items for a report.

    Args:
        report_id: Report ID
        db: Database session

    Returns:
        List of cash flow items
    """
    repository = CashFlowItemRepository(db)
    items = repository.get_by_report_id(report_id)
    return [CashFlowItemResponse.model_validate(item) for item in items]
