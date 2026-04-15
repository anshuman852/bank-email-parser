"""Shared helpers for Kotak parser modules."""

from bank_email_parser.parsing.dates import parse_datetime


def _parse_kotak_datetime(date_str: str, time_str: str | None = None):
    """Parse a Kotak date (and optional time) via dateutil."""
    if time_str:
        return parse_datetime(f"{date_str.strip()} {time_str.strip()}")
    return parse_datetime(date_str)
