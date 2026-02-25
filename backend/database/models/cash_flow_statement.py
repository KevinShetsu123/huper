"""Cash Flow Item Model"""

from sqlalchemy.sql.sqltypes import (
    Integer, String, BigInteger, SmallInteger, Unicode
)
from sqlalchemy.sql.schema import Column, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from backend.database.database import Base


class CashFlowItem(Base):
    """Cash Flow Item Model"""
    __tablename__ = "cash_flow_statement_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(
        Integer,
        ForeignKey("financial_reports.id"),
        nullable=False, index=True
    )
    item_name = Column(Unicode(255), nullable=False)
    item_code = Column(String(16), nullable=True)
    item_value = Column(BigInteger, nullable=False)
    sign = Column(SmallInteger, nullable=False)
    parent_item_id = Column(String(16), nullable=True)
    level = Column(Integer, nullable=False)
    item_display = Column(Integer, nullable=False)

    # Relationships
    report = relationship("FinancialReport", back_populates="cash_flow_items")

    __table_args__ = (
        CheckConstraint("sign IN (1, -1)", name="chk_cf_sign"),
    )
