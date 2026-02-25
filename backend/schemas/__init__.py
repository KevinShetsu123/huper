"""Schemas package."""

from backend.schemas.scraper import (
    FinancialReportBase,
    FinancialReportCreate,
    FinancialReportInDB,
    FinancialReportResponse,
    ScraperRequest,
    ScraperResponse,
    BulkScraperRequest,
    BulkScraperResponse,
)

from backend.schemas.financial import (
    BalanceSheetItemCreate,
    BalanceSheetItemResponse,
    IncomeStatementItemCreate,
    IncomeStatementItemResponse,
    CashFlowItemCreate,
    CashFlowItemResponse,
    FinancialStatementsCreate,
    FinancialStatementsResponse,
)

__all__ = [
    "FinancialReportBase",
    "FinancialReportCreate",
    "FinancialReportInDB",
    "FinancialReportResponse",
    "ScraperRequest",
    "ScraperResponse",
    "BulkScraperRequest",
    "BulkScraperResponse",
    "BalanceSheetItemCreate",
    "BalanceSheetItemResponse",
    "IncomeStatementItemCreate",
    "IncomeStatementItemResponse",
    "CashFlowItemCreate",
    "CashFlowItemResponse",
    "FinancialStatementsCreate",
    "FinancialStatementsResponse",
]
