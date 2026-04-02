"""Tests for newly added parsers: Kotak811 Transaction, Kotak CC Bill Paid,
ICICI CC Reversal (stub), and Axis NEFT (stub)."""

from decimal import Decimal

import pytest

from bank_email_parser.api import parse_email
from bank_email_parser.exceptions import ParseError


class TestKotak811TransactionParser:
    """Test Kotak811TransactionParser with synthetic HTML matching the observed format."""

    SAMPLE_HTML = """
    <html><body>
    <table width="100%">
      <tr><td>Hello Sample Customer Name,</td></tr>
      <tr><td>Your transaction for INR 4321.00 has been processed successfully.
        Here are your transaction details.</td></tr>
      <tr><td>Transaction ID: Ab3Xy7MnP5QrS9t246UvW8</td></tr>
      <tr><td>Amount: INR 4321.00</td></tr>
      <tr><td>Status: Successful</td></tr>
      <tr><td>Team Kotak811,</td></tr>
    </table>
    </body></html>
    """

    def test_parses_kotak811_transaction(self):
        result = parse_email("kotak", self.SAMPLE_HTML)
        assert result.email_type == "kotak811_transaction"
        assert result.bank == "kotak"
        assert result.transaction.direction == "debit"
        assert result.transaction.amount.amount == Decimal("4321.00")
        assert result.transaction.amount.currency == "INR"
        assert result.transaction.reference_number == "Ab3Xy7MnP5QrS9t246UvW8"

    def test_parses_rupee_symbol(self):
        html = """
        <html><body>
        <table>
          <tr><td>Your transaction for ₹ 12345.00 has been processed successfully.</td></tr>
          <tr><td>Transaction ID: Cd4Za8LpR6TuV1w357XyQ9</td></tr>
          <tr><td>Amount: ₹ 12345.00</td></tr>
          <tr><td>Status: SUCCESS</td></tr>
        </table>
        </body></html>
        """
        result = parse_email("kotak", html)
        assert result.email_type == "kotak811_transaction"
        assert result.transaction.amount.amount == Decimal("12345.00")
        assert result.transaction.reference_number == "Cd4Za8LpR6TuV1w357XyQ9"


class TestKotakCcBillPaidParser:
    """Test KotakCcBillPaidParser with synthetic HTML matching the observed format."""

    SAMPLE_HTML = """
    <html><body>
    <table width="100%">
      <tr><td>
        <p>
          Hello CUSTOMER,<br><br>
          Your credit card bill was paid successfully!<br><br>
          Bank: ICICI Credit card<br>
          Card no: **** 4242<br>
          Bill amount: ₹2,345<br>
          Paid on: 14 March 2024<br><br>
          Digitally yours,<br>
          Kotak811
        </p>
      </td></tr>
    </table>
    </body></html>
    """

    def test_parses_cc_bill_paid(self):
        result = parse_email("kotak", self.SAMPLE_HTML)
        assert result.email_type == "kotak_cc_bill_paid"
        assert result.bank == "kotak"
        assert result.transaction.direction == "debit"
        assert result.transaction.amount.amount == Decimal("2345")
        assert result.transaction.amount.currency == "INR"
        assert result.transaction.card_mask == "**** 4242"

    def test_parses_date(self):
        result = parse_email("kotak", self.SAMPLE_HTML)
        assert result.transaction.transaction_date is not None
        assert result.transaction.transaction_date.year == 2024
        assert result.transaction.transaction_date.month == 3
        assert result.transaction.transaction_date.day == 14

    def test_extracts_bank_as_counterparty(self):
        result = parse_email("kotak", self.SAMPLE_HTML)
        assert result.transaction.counterparty is not None
        assert "ICICI" in result.transaction.counterparty

    def test_parses_hsbc_variant(self):
        html = """
        <html><body>
        <p>
          Hello CUSTOMER,<br><br>
          Your credit card bill was paid successfully!<br><br>
          Bank: HSBC Credit Card<br>
          Card no: **** 5151<br>
          Bill amount: ₹2,345<br>
          Paid on: 09 March 2024<br><br>
        </p>
        </body></html>
        """
        result = parse_email("kotak", html)
        assert result.email_type == "kotak_cc_bill_paid"
        assert result.transaction.card_mask == "**** 5151"
        assert "HSBC" in result.transaction.counterparty

    def test_parses_large_amount_with_commas(self):
        html = """
        <html><body>
        <p>
          Your credit card bill was paid successfully!<br>
          Bank: ICICI Credit card<br>
          Card no: **** 4242<br>
          Bill amount: ₹2,64,831.40<br>
          Paid on: 22 March 2024<br>
        </p>
        </body></html>
        """
        result = parse_email("kotak", html)
        assert result.transaction.amount.amount == Decimal("264831.40")


class TestIciciCcReversalStub:
    """Test that the ICICI CC Reversal parser raises NotImplementedError."""

    def test_raises_not_implemented(self):
        """The stub should raise ParseError (wrapping NotImplementedError)
        when no other parser matches and reversal format is encountered."""
        html = "<html><body>Reversal processed on your ICICI Bank Credit Card</body></html>"
        with pytest.raises(ParseError):
            parse_email("icici", html)


class TestAxisNeftStub:
    """Test that the Axis NEFT parser raises NotImplementedError."""

    def test_raises_not_implemented(self):
        """The stub should raise ParseError (wrapping NotImplementedError)
        when no other parser matches."""
        html = "<html><body>NEFT is initiated from your Axis Bank account</body></html>"
        with pytest.raises(ParseError):
            parse_email("axis", html)
