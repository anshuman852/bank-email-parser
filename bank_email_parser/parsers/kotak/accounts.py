"""Kotak account credit and mandate email parsers."""

import re

from bank_email_parser.exceptions import ParseError
from bank_email_parser.models import Money, ParsedEmail, TransactionAlert
from bank_email_parser.parsers.base import BaseEmailParser
from bank_email_parser.utils import parse_amount, parse_date

from ._common import _parse_kotak_datetime


class KotakImpsCreditParser(BaseEmailParser):
    """Kotak Bank IMPS incoming credit."""

    bank = "kotak"
    email_type = "kotak_imps_credit"

    _pattern = re.compile(
        r"your\s+account\s+"
        r"(?P<account>\w+\s*\d{4})"
        r"\s+is\s+credited\s+by\s+"
        r"(?:Rs\.?\s*|INR\s*)(?P<amount>[\d,]+(?:\.\d+)?)"
        r"\s+on\s+"
        r"(?P<date>\d{1,2}-[A-Za-z]{3}-\d{2,4})"
        r"\s+for\s+IMPS\s+transaction",
        re.IGNORECASE,
    )
    _sender_pattern = re.compile(
        r"Sender\s+Name\s*:\s*(?P<sender>.+?)(?:\s*Sender\s+Mobile|\s*$)",
        re.IGNORECASE,
    )
    _imps_ref_pattern = re.compile(
        r"IMPS\s+Reference\s+No\s*:\s*(?P<ref>\d+)",
        re.IGNORECASE,
    )

    def parse(self, html: str) -> ParsedEmail:
        _, text = self.prepare_html(html)
        if not (match := self._pattern.search(text)):
            raise ParseError("Could not parse Kotak IMPS credit.")
        if (amount := parse_amount(match.group("amount"))) is None:
            raise ParseError(f"Could not parse amount: {match.group('amount')!r}")

        counterparty = None
        if sender_match := self._sender_pattern.search(text):
            counterparty = sender_match.group("sender").strip()

        reference_number = None
        if ref_match := self._imps_ref_pattern.search(text):
            reference_number = ref_match.group("ref")

        return ParsedEmail(
            email_type=self.email_type,
            bank=self.bank,
            transaction=TransactionAlert(
                direction="credit",
                amount=Money(amount=amount),
                transaction_date=parse_date(match.group("date")),
                counterparty=counterparty,
                reference_number=reference_number,
                account_mask=match.group("account").strip(),
                channel="imps",
                raw_description=match.group(0).strip(),
            ),
        )


class KotakNeftCreditParser(BaseEmailParser):
    """Kotak Bank NEFT incoming credit."""

    bank = "kotak"
    email_type = "kotak_neft_credit"

    _pattern = re.compile(
        r"(?:Rs\.?|₹|INR)\s*(?P<amount>[\d,]+(?:\.\d+)?)\s+"
        r"has\s+been\s+credited\s+to\s+your\s+Kotak\s+Bank\s+a/c\s+(?P<account>\w+)\s+"
        r"on\s+(?P<date>\d{1,2}-\w{3}-\d{2,4})\s+"
        r"via\s+NEFT\s+transaction\s+from\s+(?P<sender>.+?)\.",
        re.IGNORECASE,
    )
    _utr_pattern = re.compile(
        r"Unique\s+Transaction\s+Reference\s+Number\s+\(UTR\)\s+is\s*:\s*(?P<utr>\S+)",
        re.IGNORECASE,
    )

    def parse(self, html: str) -> ParsedEmail:
        _, text = self.prepare_html(html)
        if not (match := self._pattern.search(text)):
            raise ParseError("Could not parse Kotak NEFT credit.")
        if (amount := parse_amount(match.group("amount"))) is None:
            raise ParseError(f"Could not parse amount: {match.group('amount')!r}")

        reference_number = None
        if utr_match := self._utr_pattern.search(text):
            reference_number = utr_match.group("utr")

        return ParsedEmail(
            email_type=self.email_type,
            bank=self.bank,
            transaction=TransactionAlert(
                direction="credit",
                amount=Money(amount=amount),
                transaction_date=parse_date(match.group("date")),
                counterparty=match.group("sender").strip(),
                account_mask=match.group("account"),
                reference_number=reference_number,
                channel="neft",
                raw_description=match.group(0).strip(),
            ),
        )


class KotakNachDebitParser(BaseEmailParser):
    """Kotak Bank NACH/ECS mandate debit."""

    bank = "kotak"
    email_type = "kotak_nach_debit"

    _pattern = re.compile(
        r"Your\s+account\s+(?P<account>\w+)\s+has\s+been\s+debited\s+"
        r"towards\s+NACH/ECS\s+transaction",
        re.IGNORECASE,
    )
    _beneficiary_pattern = re.compile(
        r"Beneficiary\s*:\s*(?P<beneficiary>.+?)(?:\s+UMRN\s+Number|\s+Amount\s*:|\s+Transaction\s+date)",
        re.IGNORECASE,
    )
    _amount_pattern = re.compile(
        r"Amount\s*:\s*(?:Rs\.?|₹|INR)\s*(?P<amount>[\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    )
    _date_pattern = re.compile(
        r"Transaction\s+date\s*:\s*(?P<date>\d{2}/\d{2}/\d{4})",
        re.IGNORECASE,
    )
    _footer_date_pattern = re.compile(
        r"sent\s+by\s+the\s+System\s*:\s*(?P<date>\d{2}/\d{2}/\d{2})\s+(?P<time>\d{2}:\d{2})",
        re.IGNORECASE,
    )

    def parse(self, html: str) -> ParsedEmail:
        _, text = self.prepare_html(html)
        if not (match := self._pattern.search(text)):
            raise ParseError("Could not parse Kotak NACH debit.")
        if not (amount_match := self._amount_pattern.search(text)):
            raise ParseError("Could not find amount in Kotak NACH debit email.")
        if (amount := parse_amount(amount_match.group("amount"))) is None:
            raise ParseError(
                f"Could not parse amount: {amount_match.group('amount')!r}"
            )

        counterparty = None
        if ben_match := self._beneficiary_pattern.search(text):
            counterparty = ben_match.group("beneficiary").strip()

        txn_date = None
        txn_time = None
        if date_match := self._date_pattern.search(text):
            txn_date = parse_date(date_match.group("date"))
        elif footer_match := self._footer_date_pattern.search(text):
            parsed = _parse_kotak_datetime(
                footer_match.group("date"),
                footer_match.group("time"),
            )
            if parsed:
                txn_date = parsed.date()
                txn_time = parsed.time()

        return ParsedEmail(
            email_type=self.email_type,
            bank=self.bank,
            transaction=TransactionAlert(
                direction="debit",
                amount=Money(amount=amount),
                transaction_date=txn_date,
                transaction_time=txn_time,
                counterparty=counterparty,
                account_mask=match.group("account"),
                channel="nach",
                raw_description=match.group(0).strip(),
            ),
        )
