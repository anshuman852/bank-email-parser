"""Date and datetime parsing helpers backed by dateutil."""

from datetime import date, datetime

from dateutil import parser as _dateutil_parser


def parse_datetime(value: str) -> datetime | None:
    """Parse a date or date+time string with dateutil (dayfirst=True)."""
    try:
        return _dateutil_parser.parse(value.strip(), dayfirst=True)
    except ValueError, TypeError, OverflowError:
        return None


def parse_date(date_str: str) -> date | None:
    """Parse a date-only string via dateutil. Returns None on failure."""
    dt = parse_datetime(date_str)
    return dt.date() if dt else None
