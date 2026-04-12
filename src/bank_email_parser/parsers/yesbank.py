"""YES BANK email parsers.

Supported email types:
- yesbank_cc_debit_alert: Credit card spend/debit alert
"""

import re
from datetime import datetime

from bank_email_parser.exceptions import ParseError
from bank_email_parser.models import Money, ParsedEmail, TransactionAlert
from bank_email_parser.parsers.base import BaseEmailParser, parse_with_parsers
from bank_email_parser.utils import parse_amount


class YesbankCcDebitAlertParser(BaseEmailParser):
    """YES BANK Credit Card debit (spend) alert.

    Matches emails like:
      'INR 1,234.56 has been spent on your YES BANK Credit Card ending with 1234
       at SAMPLE MERCHANT on 01-01-2026 at 08:30:15 pm. Avl Bal INR 50,000.00.'
    """

    bank = "yesbank"
    email_type = "yesbank_cc_debit_alert"

    _pattern = re.compile(
        r"INR\s+([\d,]+(?:\.\d{2})?)\s+has been spent on your YES BANK Credit Card ending with (\d{4})\s+"
        r"at (.+?) on (\d{2}-\d{2}-\d{4}) at (\d{2}:\d{2}:\d{2})\s*(am|pm)"
        r"(?:\.\s*Avl Bal\s+INR\s+([\d,]+(?:\.\d{2})?))?",
        re.IGNORECASE,
    )

    def parse(self, html: str) -> ParsedEmail:
        _, text = self.prepare_html(html)

        if not (match := self._pattern.search(text)):
            raise ParseError("Could not parse YES BANK CC debit alert.")

        amount = parse_amount(match.group(1))
        if amount is None:
            raise ParseError(f"Could not parse amount: {match.group(1)!r}")

        card_mask = match.group(2)
        counterparty = match.group(3).strip() or None

        # Parse date + time together
        date_str = match.group(4)
        time_str = match.group(5)
        ampm = match.group(6).lower()

        txn_date = None
        txn_time = None
        try:
            dt = datetime.strptime(
                f"{date_str} {time_str} {ampm}", "%d-%m-%Y %I:%M:%S %p"
            )
            txn_date = dt.date()
            txn_time = dt.time()
        except ValueError:
            # Fallback: try date only
            try:
                txn_date = datetime.strptime(date_str, "%d-%m-%Y").date()
            except ValueError:
                pass

        # Available balance (optional)
        balance = None
        if match.group(7):
            bal_amount = parse_amount(match.group(7))
            if bal_amount is not None:
                balance = Money(amount=bal_amount)

        return ParsedEmail(
            email_type=self.email_type,
            bank=self.bank,
            transaction=TransactionAlert(
                direction="debit",
                amount=Money(amount=amount),
                transaction_date=txn_date,
                transaction_time=txn_time,
                counterparty=counterparty,
                card_mask=card_mask,
                channel="card",
                balance=balance,
                raw_description=match.group(0).strip(),
            ),
        )


_PARSERS = (YesbankCcDebitAlertParser(),)


def parse(html: str) -> ParsedEmail:
    return parse_with_parsers("yesbank", html, _PARSERS)
