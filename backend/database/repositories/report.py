"""Repository for Financial Report database operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm.session import Session
from sqlalchemy import func
from sqlalchemy.sql.expression import and_, select, delete
from backend.database.models import FinancialReport


class ReportRepository:
    """Repository class for managing financial reports in the database."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        self.session = session

    def add(self, report_data: Dict[str, Any]) -> FinancialReport:
        """Add a single financial report to the database.

        Args:
            report_data (dict): Dictionary containing report fields

        Returns:
            FinancialReport: The created report object
        """
        report = FinancialReport(**report_data)
        self.session.add(report)
        self.session.commit()
        self.session.refresh(report)
        return report

    def add_bulk(
        self, reports_data: List[Dict[str, Any]]
    ) -> List[FinancialReport]:
        """Add multiple financial reports to the database in bulk.

        Args:
            reports_data (list): List of dictionaries containing report fields

        Returns:
            list: List of created report objects
        """
        reports = [FinancialReport(**data) for data in reports_data]
        self.session.bulk_save_objects(reports, return_defaults=True)
        self.session.commit()
        return reports

    def get_by_id(self, report_id: int) -> Optional[FinancialReport]:
        """Get a financial report by its ID.

        Args:
            report_id (int): The ID of the report

        Returns:
            FinancialReport or None: The report if found, None otherwise
        """
        stmt = select(FinancialReport).where(FinancialReport.id == report_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_symbol(self, symbol: str) -> List[FinancialReport]:
        """Get all reports for a specific stock symbol.

        Args:
            symbol (str): Stock symbol

        Returns:
            list: List of financial reports
        """
        stmt = select(FinancialReport).where(
            FinancialReport.symbol == symbol.lower()
        )
        return list(self.session.execute(stmt).scalars().all())

    def find_duplicate(
        self,
        symbol: str,
        report_type: str,
        report_year: int,
        report_quarter: Optional[int] = None,
    ) -> Optional[FinancialReport]:
        """Find a duplicate report based on unique identifiers.

        Args:
            symbol (str): Stock symbol
            report_type (str): Type of report ('annual' or 'quarterly')
            report_year (int): Year of the report
            report_quarter (int, optional): Quarter of the report (1-4)

        Returns:
            FinancialReport or None: Existing report if found, None otherwise
        """
        stmt = select(FinancialReport).where(
            and_(
                FinancialReport.symbol == symbol.lower(),
                FinancialReport.report_type == report_type,
                FinancialReport.report_year == report_year,
            )
        )

        if report_quarter is not None:
            stmt = stmt.where(FinancialReport.report_quarter == report_quarter)
        else:
            stmt = stmt.where(FinancialReport.report_quarter.is_(None))

        return self.session.execute(stmt).scalar_one_or_none()

    def update(
        self, report_id: int, update_data: Dict[str, Any]
    ) -> Optional[FinancialReport]:
        """Update an existing financial report.

        Args:
            report_id (int): ID of the report to update
            update_data (dict): Dictionary containing fields to update

        Returns:
            FinancialReport or None: Updated report if found, None otherwise
        """
        report = self.get_by_id(report_id)
        if report:
            for key, value in update_data.items():
                if hasattr(report, key):
                    setattr(report, key, value)
            self.session.commit()
            self.session.refresh(report)
        return report

    def upsert(
        self, report_data: Dict[str, Any]
    ) -> tuple[FinancialReport, bool]:
        """Insert or update a report if it already exists.

        Args:
            report_data (dict): Dictionary containing report fields

        Returns:
            tuple: (FinancialReport, created) where created is True if new,
            False if updated
        """
        existing = self.find_duplicate(
            symbol=report_data["symbol"],
            report_type=report_data["report_type"],
            report_year=report_data["report_year"],
            report_quarter=report_data.get("report_quarter"),
        )

        if existing:
            for key, value in report_data.items():
                if hasattr(existing, key) and key != "id":
                    setattr(existing, key, value)
            self.session.commit()
            self.session.refresh(existing)
            return existing, False
        else:
            new_report = FinancialReport(**report_data)
            self.session.add(new_report)
            self.session.commit()
            self.session.refresh(new_report)
            return new_report, True

    def upsert_bulk(
        self, reports_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Insert or update multiple reports in bulk.

        Args:
            reports_data (list): List of dictionaries containing report fields

        Returns:
            dict: Statistics with 'created' and 'updated' counts
        """
        created_count = 0
        updated_count = 0

        for report_data in reports_data:
            _, created = self.upsert(report_data)
            if created:
                created_count += 1
            else:
                updated_count += 1

        return {
            "created": created_count,
            "updated": updated_count,
            "total": len(reports_data),
        }

    def delete(self, report_id: int) -> bool:
        """Delete a financial report by ID.

        Args:
            report_id (int): ID of the report to delete

        Returns:
            bool: True if deleted, False if not found
        """
        report = self.get_by_id(report_id)
        if report:
            self.session.delete(report)
            self.session.commit()
            return True
        return False

    def delete_by_symbol(self, symbol: str) -> int:
        """Delete all reports for a specific symbol.

        Args:
            symbol (str): Stock symbol

        Returns:
            int: Number of reports deleted
        """
        stmt = delete(FinancialReport).where(
            FinancialReport.symbol == symbol.lower()
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount

    def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[FinancialReport]:
        """Get all financial reports with optional pagination.

        Args:
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip

        Returns:
            list: List of financial reports
        """
        stmt = select(FinancialReport).order_by(
            FinancialReport.symbol,
            FinancialReport.report_year.desc(),
            FinancialReport.report_quarter,
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars().all())

    def count(self) -> int:
        """Count total number of reports in the database.

        Returns:
            int: Total count of reports
        """
        stmt = select(func.count()).select_from(FinancialReport)
        return self.session.execute(stmt).scalar()

    def count_by_symbol(self, symbol: str) -> int:
        """Count reports for a specific symbol.

        Args:
            symbol (str): Stock symbol

        Returns:
            int: Count of reports for the symbol
        """
        stmt = (
            select(func.count())
            .select_from(FinancialReport)
            .where(FinancialReport.symbol == symbol.lower())
        )
        return self.session.execute(stmt).scalar()
