"""Kotak811 and digital transaction email parsers."""

import re

from bank_email_parser.exceptions import ParseError
from bank_email_parser.models import Money, ParsedEmail, TransactionAlert
from bank_email_parser.parsers.base import BaseEmailParser
from bank_email_parser.utils import parse_amount


class KotakDigitalTransactionParser(BaseEmailParser):
    """Kotak811 digital transaction (minimal data)."""

    bank = "kotak"
    email_type = "kotak_digital_transaction"

    _amount_pattern = re.compile(
        r"Your\s+transaction\s+of\s+(?:Rs\.?|₹|INR)\s*(?P<amount>[\d,]+(?:\.\d+)?)\s+"
        r"has\s+been\s+processed\s+successfully",
        re.IGNORECASE,
    )

    def parse(self, html: str) -> ParsedEmail:
        soup, text = self.prepare_html(html)
        if not (match := self._amount_pattern.search(text)):
            raise ParseError("Could not parse Kotak digital transaction.")
        if (amount := parse_amount(match.group("amount"))) is None:
            raise ParseError(f"Could not parse amount: {match.group('amount')!r}")

        reference_number = None
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                header = cells[0].get_text(strip=True).lower()
                if "transaction id" in header:
                    reference_number = cells[1].get_text(strip=True)
                    break

        return ParsedEmail(
            email_type=self.email_type,
            bank=self.bank,
            transaction=TransactionAlert(
                direction="debit",
                amount=Money(amount=amount),
                reference_number=reference_number,
                raw_description=match.group(0).strip(),
            ),
        )


class Kotak811TransactionParser(BaseEmailParser):
    """Kotak811 app transaction (from no-reply@kotak.com)."""

    bank = "kotak"
    email_type = "kotak811_transaction"

    _amount_pattern = re.compile(
        r"Your\s+transaction\s+for\s+(?:Rs\.?|₹|INR)\s*(?P<amount>[\d,]+(?:\.\d+)?)\s+"
        r"has\s+been\s+processed\s+successfully",
        re.IGNORECASE,
    )
    _txn_id_pattern = re.compile(
        r"Transaction\s+ID\s*:\s*(?P<txn_id>\S+)",
        re.IGNORECASE,
    )

    def parse(self, html: str) -> ParsedEmail:
        _, text = self.prepare_html(html)
        if not (match := self._amount_pattern.search(text)):
            raise ParseError("Could not parse Kotak811 transaction.")
        if (amount := parse_amount(match.group("amount"))) is None:
            raise ParseError(f"Could not parse amount: {match.group('amount')!r}")

        reference_number = None
        if txn_match := self._txn_id_pattern.search(text):
            reference_number = txn_match.group("txn_id")

        return ParsedEmail(
            email_type=self.email_type,
            bank=self.bank,
            transaction=TransactionAlert(
                direction="debit",
                amount=Money(amount=amount),
                reference_number=reference_number,
                raw_description=match.group(0).strip(),
            ),
        )
