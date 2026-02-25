"""
Financial report metadata parser.

This module processes raw scraped financial report data into structured format
suitable for database insertion. It handles:
- Filtering parent company reports
- Determining audit status
- Parsing report periods
- Prioritizing audited reports
"""
import re
import logging
from typing import List, Dict, Any, cast
import pandas as pd


logger = logging.getLogger(__name__)


def filter_parent_company(
    reports: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Filter out parent company reports.

    Removes reports that contain 'mẹ' (parent company) in the report name.

    Args:
        reports (List[Dict[str, Any]]): List of report dictionaries

    Returns:
        List[Dict[str, Any]]: Filtered list excluding parent company reports
    """
    filtered = []
    for report in reports:
        report_name = report.get('report_name', '')
        if report_name and 'mẹ' not in report_name.lower():
            filtered.append(report)

    return filtered


def determine_audit_status(report_name: str) -> Dict[str, bool]:
    """Determine if a report is audited or reviewed.

    Args:
        report_name (str): The name of the financial report

    Returns:
        Dict[str, bool]: Dictionary with 'is_audited' and 'is_reviewed' keys
    """
    if not report_name:
        return {'is_audited': False, 'is_reviewed': False}

    report_name_lower = report_name.lower()
    is_audited = 'kiểm toán' in report_name_lower
    is_reviewed = 'soát xét' in report_name_lower

    return {
        'is_audited': is_audited,
        'is_reviewed': is_reviewed
    }


def parse_report_time(report_time: str) -> Dict[str, Any]:
    """Parse report_time string into structured components.

    Parses report period like 'Q3/2025' or 'CN/2025' into:
    - report_type: 'quarterly' or 'annual'
    - report_year: integer year
    - report_quarter: integer quarter (1-4) or None

    Args:
        report_time (str): Report time string (e.g., 'Q3/2025', 'CN/2025')

    Returns:
        Dict[str, Any]: Dictionary with report_type, report_year,
        report_quarter
    """
    if not report_time or '/' not in report_time:
        return {
            'report_type': None,
            'report_year': None,
            'report_quarter': None
        }

    try:
        parts = report_time.split('/')
        period = parts[0].strip().upper()
        year = int(parts[1].strip())

        if period.startswith('Q'):
            try:
                quarter = int(period[1:])
                if 1 <= quarter <= 4:
                    return {
                        'report_type': 'quarterly',
                        'report_year': year,
                        'report_quarter': quarter
                    }
            except (ValueError, IndexError):
                pass
        elif period in ['CN', 'NAM', 'YEAR']:
            return {
                'report_type': 'annual',
                'report_year': year,
                'report_quarter': None
            }

        return {
            'report_type': None,
            'report_year': year,
            'report_quarter': None
        }

    except (ValueError, IndexError) as error:
        logger.warning(
            "Failed to parse report_time '%s': %s", report_time, error
        )

        return {
            'report_type': None,
            'report_year': None,
            'report_quarter': None
        }


def clean_report_name(report_name: str) -> str:
    """Clean report name by removing parenthetical content.

    Args:
        report_name (str): Original report name

    Returns:
        str: Cleaned report name
    """

    if not report_name:
        return report_name

    cleaned = re.sub(r'\s*\([^)]*\)', '', report_name)
    return cleaned.strip()


def prioritize_reports(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prioritize audited and reviewed reports over regular reports.

    For duplicate reports (same symbol, report_type, report_year,
    report_quarter), keep only the one with highest priority:
    1. Audited reports (is_audited=True)
    2. Reviewed reports (is_reviewed=True)
    3. Regular reports

    Args:
        reports (List[Dict[str, Any]]): List of reports with audit status

    Returns:
        List[Dict[str, Any]]: Deduplicated list with prioritized reports
    """
    if not reports:
        return reports

    df = pd.DataFrame(reports)
    df['priority'] = (
        df['is_audited'].astype(int) * 2 +
        df['is_reviewed'].astype(int)
    )
    df = df.sort_values('priority', ascending=False)
    df = df.drop_duplicates(
        subset=['symbol', 'report_type', 'report_year', 'report_quarter'],
        keep='first'
    )
    df = df.drop(columns=['priority'])

    return cast(List[Dict[str, Any]], df.to_dict('records'))


def process_reports(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process raw financial report data into structured format.

    This function performs the following operations:
    1. Filters out parent company reports
    2. Determines audit and review status
    3. Parses report_time into type, year, and quarter
    4. Cleans report names
    5. Prioritizes audited and reviewed reports
    6. Sorts reports by symbol, year, and quarter

    Args:
        reports (List[Dict[str, Any]]): List of raw report dictionaries

    Returns:
        List[Dict[str, Any]]: Processed list of report dictionaries in JSON
        format
    """
    if not reports:
        logger.warning("No reports to process")
        return []

    reports = filter_parent_company(reports)
    if not reports:
        logger.warning("All reports filtered out (parent company)")
        return []

    for report in reports:
        audit_status = determine_audit_status(report.get('report_name', ''))
        report['is_audited'] = audit_status['is_audited']
        report['is_reviewed'] = audit_status['is_reviewed']

    for report in reports:
        time_parsed = parse_report_time(report.get('report_time', ''))
        report['report_type'] = time_parsed['report_type']
        report['report_year'] = time_parsed['report_year']
        report['report_quarter'] = time_parsed['report_quarter']

    for report in reports:
        if report.get('report_name'):
            report['report_name'] = clean_report_name(report['report_name'])

    reports = prioritize_reports(reports)
    df = pd.DataFrame(reports)
    df = df.sort_values(
        by=['symbol', 'report_year', 'report_quarter'],
        ascending=[True, False, True],
        na_position='last'
    )

    column_order = [
        'symbol',
        'company_name',
        'report_name',
        'report_type',
        'report_year',
        'report_quarter',
        'is_audited',
        'is_reviewed',
        'report_url'
    ]

    existing_columns = [col for col in column_order if col in df.columns]
    df = df[existing_columns]
    result = df.to_dict('records')

    for report in result:
        for key, value in report.items():
            if pd.isna(value):
                report[key] = None

    logger.info("Processed %d reports", len(result))

    return cast(List[Dict[str, Any]], result)
