"""Financial Report Model"""

from sqlalchemy.sql.sqltypes import Integer, String, Boolean, Unicode
from sqlalchemy.sql.schema import Column, CheckConstraint
from sqlalchemy.orm import relationship
from backend.database.database import Base


class FinancialReport(Base):
    """Financial Report Model"""
    __tablename__ = "financial_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False)
    company_name = Column(Unicode(255), nullable=False)
    report_name = Column(Unicode(255), nullable=False)
    report_type = Column(String(50), nullable=False)
    report_year = Column(Integer, nullable=False)
    report_quarter = Column(Integer, nullable=True)
    is_audited = Column(Boolean, nullable=False, default=False)
    is_reviewed = Column(Boolean, nullable=False, default=False)
    report_url = Column(Unicode, nullable=False)

    # Relationships
    balance_sheet_items = relationship(
        "BalanceSheetItem",
        back_populates="report",
        cascade="all, delete-orphan"
    )
    income_statement_items = relationship(
        "IncomeStatementItem",
        back_populates="report",
        cascade="all, delete-orphan"
    )
    cash_flow_items = relationship(
        "CashFlowItem",
        back_populates="report",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "(report_type = 'annual' AND report_quarter IS NULL) OR "
            "(report_type = 'quarterly' AND report_quarter BETWEEN 1 AND 4)",
            name="chk_report_quarter"
        ),
    )
