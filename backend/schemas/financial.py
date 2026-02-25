"""Pydantic schemas for API request/response validation."""

from typing import Optional, List
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator
)

from backend.schemas import (
    FinancialReportCreate,
    FinancialReportResponse
)


class FinancialItemBase(BaseModel):
    """
    Base schema for 3 tables:
        1. Balance Sheet Items
        2. Income Statement Items
        3. Cash Flow Items
    """
    item_name: str = Field(
        ..., max_length=255, description="Name of the financial item"
    )
    item_code: Optional[str] = Field(
        None, max_length=16, description="Code of the financial item"
    )
    item_value: int = Field(
        ..., description="Value of the financial item"
    )
    sign: int = Field(
        ..., description="Sign: 1 for positive, -1 for negative"
    )
    level: int = Field(
        ..., ge=1, description="Hierarchy level of the item"
    )
    item_display: int = Field(
        ..., ge=1, description="Display order of the item"
    )
    parent_item_id: Optional[str] = Field(
        None, description="Code of the parent item"
    )

    @field_validator('sign')
    @classmethod
    def validate_sign(cls, value):
        """Validate sign is either 1 or -1."""
        if value not in [1, -1]:
            raise ValueError("sign must be 1 or -1")
        return value


class FinancialItemCreate(FinancialItemBase):
    """Schema for creating financial items (without report_id)."""
    report_id: int = Field(
        ..., description="ID of the associated financial report"
    )


class FinancialItemResponse(FinancialItemCreate):
    """Schema for financial item response."""
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Item ID")


class BalanceSheetItemCreate(FinancialItemBase):
    """Schema for creating balance sheet item."""
    report_id: int


class BalanceSheetItemResponse(BalanceSheetItemCreate):
    """Schema for balance sheet item response."""
    model_config = ConfigDict(from_attributes=True)
    id: int


class IncomeStatementItemCreate(FinancialItemBase):
    """Schema for creating income statement item."""
    report_id: int


class IncomeStatementItemResponse(IncomeStatementItemCreate):
    """Schema for income statement item response."""
    model_config = ConfigDict(from_attributes=True)
    id: int


class CashFlowItemCreate(FinancialItemBase):
    """Schema for creating cash flow item."""
    report_id: int


class CashFlowItemResponse(CashFlowItemCreate):
    """Schema for cash flow item response."""
    model_config = ConfigDict(from_attributes=True)
    id: int


class FinancialStatementsCreate(BaseModel):
    """
    Schema for creating complete financial data including report and all items.
    """
    financial_reports: List[FinancialReportCreate]
    balance_sheet_items: List[BalanceSheetItemCreate]
    income_statement_items: List[IncomeStatementItemCreate]
    cash_flow_items: List[CashFlowItemCreate]


class FinancialStatementsResponse(BaseModel):
    """Schema for response after creating complete financial data."""
    report: FinancialReportResponse
    balance_sheet_items_count: int
    income_statement_items_count: int
    cash_flow_items_count: int
    message: str
