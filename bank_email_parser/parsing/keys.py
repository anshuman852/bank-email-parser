"""Key normalization helpers for parser table lookups."""

import re

_KEY_CLEANUP = re.compile(r"[^a-z0-9\s]")
_WHITESPACE = re.compile(r"\s+")


def normalize_key(raw: str) -> str:
    """Normalize a table header/key for consistent lookup."""
    cleaned = _KEY_CLEANUP.sub("", raw.lower())
    return _WHITESPACE.sub(" ", cleaned).strip()
