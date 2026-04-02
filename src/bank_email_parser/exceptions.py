"""Exception types raised during email parsing."""
class ParseError(Exception):
    """Raised when an email cannot be parsed despite matching the expected type."""


class UnsupportedEmailTypeError(Exception):
    """Raised when the given email_type has no registered parser."""
