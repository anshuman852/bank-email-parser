"""Shared parsing utilities: date/amount parsing, HTML table extraction, text normalization."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup
from dateutil import parser as _dateutil_parser

from bank_email_parser.models import Money

_KEY_CLEANUP = re.compile(r"[^a-z0-9\s]")
_WHITESPACE = re.compile(r"\s+")


def normalize_key(raw: str) -> str:
    """Normalize a table header/key for consistent lookup.

    Strips punctuation, collapses whitespace, lowercases.
    'Transaction date:' -> 'transaction date'
    """
    cleaned = _KEY_CLEANUP.sub("", raw.lower())
    return _WHITESPACE.sub(" ", cleaned).strip()


def parse_datetime(value: str) -> datetime | None:
    """Parse a date or date+time string with dateutil (dayfirst=True).

    Handles the wide variety of Indian bank date formats without needing
    a format list: 19-Mar-26, 19/03/2026, 28-MAR-2026, 07 Feb 2026,
    'Mar 15, 2026 14:30:00', '15 Jan, 2026 at 16:35:07', etc.

    Returns None on failure.
    """
    try:
        return _dateutil_parser.parse(value.strip(), dayfirst=True)
    except (ValueError, TypeError, OverflowError):
        return None


def parse_date(date_str: str) -> date | None:
    """Parse a date-only string via dateutil. Returns None on failure."""
    dt = parse_datetime(date_str)
    return dt.date() if dt else None


def parse_amount(raw: str) -> Decimal | None:
    """Parse an amount string like '₹57,055.44' or '1,00,000.00' into Decimal.

    Strips currency symbols, commas, whitespace (including non-breaking spaces).
    Returns None on failure.
    """
    cleaned = raw.replace("₹", "").replace("Rs.", "").replace("Rs", "")
    cleaned = cleaned.replace(",", "").replace("\xa0", "").replace("\u200c", "").strip()
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_money(raw: str, currency: str = "INR") -> Money | None:
    """Parse a raw amount string into a Money object. Returns None on failure."""
    amount = parse_amount(raw)
    if amount is None:
        return None
    return Money(amount=amount, currency=currency)


def extract_table_pairs(
    soup: BeautifulSoup,
    expected_keys: set[str] | None = None,
) -> dict[str, str]:
    """Extract key-value pairs from 2-column table rows in HTML.

    Keys are normalized (lowercased, punctuation stripped).
    If expected_keys is provided, only those keys are included.
    Uses find_all("td", recursive=False) to avoid picking up nested table cells.
    """
    data: dict[str, str] = {}
    for row in soup.find_all("tr"):
        cells = row.find_all("td", recursive=False)
        if len(cells) != 2:
            continue
        key = normalize_key(cells[0].get_text(strip=True))
        value = cells[1].get_text(strip=True)
        if not key or not value:
            continue
        if expected_keys is not None and key not in expected_keys:
            continue
        data[key] = value
    return data


def normalize_whitespace(text: str) -> str:
    """Collapse all whitespace (including non-breaking spaces) to single spaces."""
    return _WHITESPACE.sub(" ", text.replace("\xa0", " ").replace("\u200c", "")).strip()
