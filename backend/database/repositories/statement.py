"""Repository classes for managing financial statement items."""

from typing import List, Dict, Any
from sqlalchemy.sql.expression import select, delete
from sqlalchemy.orm.session import Session
from backend.database.models import (
    BalanceSheetItem,
    IncomeStatementItem,
    CashFlowItem
)
from backend.database.repositories import ReportRepository


class BalanceSheetItemRepository:
    """Repository class for managing balance sheet items."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def add_bulk(
        self,
        items_data: List[Dict[str, Any]],
        report_id: int,
        item_code_map: Dict[str, int]
    ) -> List[BalanceSheetItem]:
        """Add multiple balance sheet items in bulk.

        Args:
            items_data: List of item data dictionaries
            report_id: ID of the financial report
            item_code_map: Mapping from item_code to actual item id

        Returns:
            List of created items
        """
        items = []
        for data in items_data:
            item_dict = data.copy()
            item_dict['report_id'] = report_id
            parent_code = item_dict.pop('parent_item_id', None)

            if parent_code and parent_code in item_code_map:
                item_dict['parent_item_id'] = item_code_map[parent_code]
            else:
                item_dict['parent_item_id'] = None

            items.append(BalanceSheetItem(**item_dict))

        self.session.add_all(items)
        self.session.flush()

        for item in items:
            if item.item_code:
                item_code_map[item.item_code] = item.id

        return items

    def get_by_report_id(self, report_id: int) -> List[BalanceSheetItem]:
        """Get all balance sheet items for a report."""
        stmt = select(BalanceSheetItem).where(
            BalanceSheetItem.report_id == report_id
        ).order_by(BalanceSheetItem.item_display)
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_report_id(self, report_id: int) -> int:
        """Delete all balance sheet items for a report."""
        stmt = delete(BalanceSheetItem).where(
            BalanceSheetItem.report_id == report_id
        )
        result = self.session.execute(stmt)
        return result.rowcount


class IncomeStatementItemRepository:
    """Repository class for managing income statement items."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def add_bulk(
        self,
        items_data: List[Dict[str, Any]],
        report_id: int,
        item_code_map: Dict[str, int]
    ) -> List[IncomeStatementItem]:
        """Add multiple income statement items in bulk.

        Args:
            items_data: List of item data dictionaries
            report_id: ID of the financial report
            item_code_map: Mapping from item_code to actual item id

        Returns:
            List of created items
        """
        items = []
        for data in items_data:
            item_dict = data.copy()
            item_dict['report_id'] = report_id

            parent_code = item_dict.pop('parent_item_id', None)
            if parent_code and parent_code in item_code_map:
                item_dict['parent_item_id'] = item_code_map[parent_code]
            else:
                item_dict['parent_item_id'] = None

            items.append(IncomeStatementItem(**item_dict))

        self.session.add_all(items)
        self.session.flush()

        for item in items:
            if item.item_code:
                item_code_map[item.item_code] = item.id

        return items

    def get_by_report_id(self, report_id: int) -> List[IncomeStatementItem]:
        """Get all income statement items for a report."""
        stmt = select(IncomeStatementItem).where(
            IncomeStatementItem.report_id == report_id
        ).order_by(IncomeStatementItem.item_display)
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_report_id(self, report_id: int) -> int:
        """Delete all income statement items for a report."""
        stmt = delete(IncomeStatementItem).where(
            IncomeStatementItem.report_id == report_id
        )
        result = self.session.execute(stmt)
        return result.rowcount


class CashFlowItemRepository:
    """Repository class for managing cash flow items."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def add_bulk(
        self,
        items_data: List[Dict[str, Any]],
        report_id: int,
        item_code_map: Dict[str, int]
    ) -> List[CashFlowItem]:
        """Add multiple cash flow items in bulk.

        Args:
            items_data: List of item data dictionaries
            report_id: ID of the financial report
            item_code_map: Mapping from item_code to actual item id

        Returns:
            List of created items
        """
        items = []
        for data in items_data:
            item_dict = data.copy()
            item_dict['report_id'] = report_id

            parent_code = item_dict.pop('parent_item_id', None)
            if parent_code and parent_code in item_code_map:
                item_dict['parent_item_id'] = item_code_map[parent_code]
            else:
                item_dict['parent_item_id'] = None

            items.append(CashFlowItem(**item_dict))

        self.session.add_all(items)
        self.session.flush()

        for item in items:
            if item.item_code:
                item_code_map[item.item_code] = item.id

        return items

    def get_by_report_id(self, report_id: int) -> List[CashFlowItem]:
        """Get all cash flow items for a report."""
        stmt = select(CashFlowItem).where(
            CashFlowItem.report_id == report_id
        ).order_by(CashFlowItem.item_display)
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_report_id(self, report_id: int) -> int:
        """Delete all cash flow items for a report."""
        stmt = delete(CashFlowItem).where(
            CashFlowItem.report_id == report_id
        )
        result = self.session.execute(stmt)
        return result.rowcount


class FinancialDataCoordinator:
    """Repository for managing complete financial data (report + all items)."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
        self.report_repo = ReportRepository(session)
        self.balance_sheet_repo = BalanceSheetItemRepository(session)
        self.income_statement_repo = IncomeStatementItemRepository(session)
        self.cash_flow_repo = CashFlowItemRepository(session)

    def add_complete_data(
        self,
        report_data: Dict[str, Any],
        balance_sheet_items: List[Dict[str, Any]],
        income_statement_items: List[Dict[str, Any]],
        cash_flow_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add complete financial data  in a single transaction.

        Args:
            report_data: Financial report data
            balance_sheet_items: List of balance sheet item data
            income_statement_items: List of income statement item data
            cash_flow_items: List of cash flow item data

        Returns:
            Dictionary with created report and item counts
        """
        try:
            report = self.report_repo.add(report_data)
            report_id = report.id

            if not isinstance(report_id, int):
                raise ValueError(
                    "Failed to retrieve report ID after insertion."
                )

            item_code_map = {}
            balance_items = self.balance_sheet_repo.add_bulk(
                balance_sheet_items,
                report_id,
                item_code_map.copy()
            )

            income_items = self.income_statement_repo.add_bulk(
                income_statement_items,
                report_id,
                item_code_map.copy()
            )

            cash_flow = self.cash_flow_repo.add_bulk(
                cash_flow_items,
                report_id,
                item_code_map.copy()
            )

            self.session.commit()

            return {
                'report': report,
                'balance_sheet_items_count': len(balance_items),
                'income_statement_items_count': len(income_items),
                'cash_flow_items_count': len(cash_flow),
                'success': True
            }

        except Exception as error:
            self.session.rollback()
            raise error
