"""Public API: parse_email() entry point and SUPPORTED_BANKS registry."""

from bank_email_parser.exceptions import ParseError, UnsupportedEmailTypeError
from bank_email_parser.models import ParsedEmail
from bank_email_parser.parsers import PARSERS

SUPPORTED_BANKS = tuple(PARSERS)


def parse_email(bank: str, html: str) -> ParsedEmail:
    """Parse an HTML email body for a given bank."""
    if not isinstance(bank, str):
        raise UnsupportedEmailTypeError(
            f"Expected 'bank' to be a string, got {type(bank).__name__}"
        )
    if not isinstance(html, str):
        raise ParseError(f"Expected 'html' to be a string, got {type(html).__name__}")

    normalized_bank = bank.strip().lower()
    if normalized_bank not in SUPPORTED_BANKS:
        raise UnsupportedEmailTypeError(
            f"Unknown bank: {normalized_bank!r}. Supported: {SUPPORTED_BANKS}"
        )
    if len(html) > 500_000:
        raise ParseError("Input HTML too large (>500KB).")

    return PARSERS[normalized_bank]().parse(html)
