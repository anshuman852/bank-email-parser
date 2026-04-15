"""Amount and currency parsing helpers."""

from decimal import Decimal, InvalidOperation

from bank_email_parser.models import Money


def parse_amount(raw: str) -> Decimal | None:
    """Parse an amount string like '₹57,055.44' into Decimal."""
    cleaned = raw.replace("₹", "").replace("Rs.", "").replace("Rs", "")
    cleaned = cleaned.replace(",", "").replace("\xa0", "").replace("\u200c", "")
    cleaned = cleaned.strip()
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
