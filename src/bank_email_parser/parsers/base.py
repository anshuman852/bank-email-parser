"""Base parser class and fallback-chain dispatcher for bank email parsers."""
from abc import ABC, abstractmethod
from collections.abc import Sequence

from bank_email_parser.exceptions import ParseError
from bank_email_parser.models import ParsedEmail


class BaseEmailParser(ABC):
    bank: str
    email_type: str

    @abstractmethod
    def parse(self, html: str) -> ParsedEmail:
        """Parse an HTML email body into a structured ParsedEmail."""
        ...


def parse_with_parsers(
    bank: str,
    html: str,
    parsers: Sequence[BaseEmailParser],
) -> ParsedEmail:
    """Try each parser in order until one succeeds."""
    errors: list[str] = []
    for parser in parsers:
        try:
            return parser.parse(html)
        except (ParseError, NotImplementedError) as exc:
            errors.append(f"{parser.email_type}: {type(exc).__name__}")

    raise ParseError(
        f"No parser for bank {bank!r} could handle this email. "
        f"Tried: {', '.join(p.email_type for p in parsers)}. "
        f"Errors: {'; '.join(errors)}"
    )
