"""
Scraper schemas for data validation.

This module defines Pydantic schemas for validating scraped financial report
data before insertion into the database. It ensures data integrity and type
safety.
"""

from typing import Optional, List
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator
)


class FinancialReportBase(BaseModel):
    """Base schema for financial report."""
    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(
        ..., min_length=1, max_length=10, description="Stock symbol"
    )
    company_name: str = Field(
        ..., min_length=1, max_length=255, description="Company name"
    )
    report_name: str = Field(
        ..., min_length=1, max_length=255, description="Report name/type"
    )
    report_type: str = Field(
        ..., description="Report type: 'quarterly' or 'annual'"
    )
    report_year: int = Field(
        ..., ge=1900, le=2100, description="Report year"
    )
    report_quarter: Optional[int] = Field(
        None, ge=1, le=4, description="Report quarter (1-4)"
    )
    is_audited: bool = Field(
        default=False, description="Whether report is audited"
    )
    is_reviewed: bool = Field(
        default=False, description="Whether report is reviewed"
    )
    report_url: str = Field(..., description="URL to download the report")

    @field_validator('report_type')
    @classmethod
    def validate_report_type(cls, value):
        """Validate report type is either 'quarterly' or 'annual'."""
        if value not in ['quarterly', 'annual']:
            raise ValueError("report_type must be 'quarterly' or 'annual'")
        return value

    @model_validator(mode='after')
    def validate_quarter_with_type(self):
        """Validate report_quarter is consistent with report_type."""
        if self.report_type == 'annual':
            if self.report_quarter is not None:
                raise ValueError(
                    "report_quarter must be None for annual reports"
                )
        elif self.report_type == 'quarterly':
            if self.report_quarter is None:
                raise ValueError(
                    "report_quarter is required for quarterly reports"
                )

            if not 1 <= self.report_quarter <= 4:
                raise ValueError("report_quarter must be between 1 and 4")
        return self

    @field_validator('symbol', 'company_name', 'report_name')
    @classmethod
    def validate_not_empty(cls, value):
        """Validate string fields are not empty or whitespace only."""
        if not value or not value.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return value.strip()


class FinancialReportCreate(FinancialReportBase):
    """Schema for creating a financial report."""


class FinancialReportInDB(FinancialReportBase):
    """Schema for financial report in database."""
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Report ID")


class FinancialReportResponse(FinancialReportInDB):
    """Schema for API response."""


class ScraperRequest(BaseModel):
    """Schema for scraper API request."""
    model_config = ConfigDict(from_attributes=True)
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock symbol to scrape"
    )
    headless: bool = Field(
        default=True,
        description="Run browser in headless mode"
    )

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, value):
        """Validate symbol format."""
        if not value or not value.strip():
            raise ValueError("symbol cannot be empty")
        return value.strip().upper()


class ScraperResponse(BaseModel):
    """Schema for scraper API response."""
    model_config = ConfigDict(from_attributes=True)
    success: bool = Field(..., description="Whether scraping was successful")
    message: str = Field(..., description="Response message")
    symbol: str = Field(..., description="Stock symbol scraped")
    reports_count: int = Field(
        default=0, description="Number of reports scraped"
    )
    created_count: int = Field(
        default=0, description="Number of reports created in DB"
    )
    updated_count: int = Field(
        default=0, description="Number of reports updated in DB"
    )
    reports: Optional[List[FinancialReportResponse]] = Field(
        default=None,
        description="List of scraped reports"
    )


class BulkScraperRequest(BaseModel):
    """Schema for bulk scraper API request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    symbols: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of stock symbols to scrape"
    )
    headless: bool = Field(
        default=True, description="Run browser in headless mode"
    )

    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, value):
        """Validate symbols list."""
        if not value:
            raise ValueError("symbols list cannot be empty")

        cleaned = []
        seen = set()
        for symbol in value:
            symbol = symbol.strip().upper()
            if symbol and symbol not in seen:
                cleaned.append(symbol)
                seen.add(symbol)

        if not cleaned:
            raise ValueError("symbols list contains no valid symbols")

        return cleaned


class BulkScraperResponse(BaseModel):
    """Schema for bulk scraper API response."""
    model_config = ConfigDict(from_attributes=True)
    success: bool = Field(
        ..., description="Whether overall scraping was successful"
    )
    message: str = Field(..., description="Response message")
    total_symbols: int = Field(
        ..., description="Total number of symbols processed")
    successful_symbols: int = Field(
        ..., description="Number of successfully scraped symbols")
    failed_symbols: int = Field(
        ..., description="Number of failed symbols")
    total_reports: int = Field(
        default=0, description="Total number of reports scraped")
    total_created: int = Field(
        default=0, description="Total reports created in DB")
    total_updated: int = Field(
        default=0, description="Total reports updated in DB")
    results: Optional[List[ScraperResponse]] = Field(
        default=None,
        description="Individual results for each symbol"
    )
