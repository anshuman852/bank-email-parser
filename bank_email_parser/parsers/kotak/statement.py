"""Kotak statement email parser."""

from bank_email_parser.exceptions import ParseError
from bank_email_parser.models import ParsedEmail
from bank_email_parser.parsers.base import BaseEmailParser


class KotakStatementEmailParser(BaseEmailParser):
    """Kotak Bank account statement email."""

    bank = "kotak"
    email_type = "kotak_account_statement"

    def parse(self, html: str) -> ParsedEmail:
        _, text = self.prepare_html(html)
        text_lower = text.lower()
        has_statement = "statement" in text_lower and "kotak" in text_lower
        has_attachment = "password-protected" in text_lower or (
            "password" in text_lower and "attached" in text_lower
        )
        if not (has_statement and has_attachment):
            raise ParseError("Not a Kotak statement email")
        return ParsedEmail(
            email_type=self.email_type,
            bank=self.bank,
            password_hint=(
                "Customer Relationship Number (CRN), "
                "or first 4 letters of name (lowercase) + DDMM of birth"
            ),
        )
