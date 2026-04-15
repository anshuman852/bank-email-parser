"""Backward-compatible re-exports for shared parsing helpers."""

from bank_email_parser.parsing import (
    extract_table_pairs,
    normalize_key,
    normalize_whitespace,
    parse_amount,
    parse_date,
    parse_datetime,
    parse_money,
)

__all__ = [
    "extract_table_pairs",
    "normalize_key",
    "normalize_whitespace",
    "parse_amount",
    "parse_date",
    "parse_datetime",
    "parse_money",
]
