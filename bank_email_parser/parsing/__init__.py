"""Parsing helpers split by concern, re-exported for staged migration."""

from bank_email_parser.parsing.amounts import parse_amount, parse_money
from bank_email_parser.parsing.dates import parse_date, parse_datetime
from bank_email_parser.parsing.html import extract_table_pairs, normalize_whitespace
from bank_email_parser.parsing.keys import normalize_key

__all__ = [
    "extract_table_pairs",
    "normalize_key",
    "normalize_whitespace",
    "parse_amount",
    "parse_date",
    "parse_datetime",
    "parse_money",
]
