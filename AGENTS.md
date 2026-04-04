# CLAUDE.md — bank-email-parser

## Project overview

`bank-email-parser` is a Python library that parses Indian bank transaction alert emails into structured Pydantic models. It supports 12 banks and ~36 distinct email formats.

Requires Python 3.14+. Dependencies: `pydantic>=2.0`, `beautifulsoup4>=4.12`.

## Project structure

```
src/bank_email_parser/
    __init__.py          # Re-exports parse_email, SUPPORTED_BANKS, models, exceptions
    api.py               # parse_email() entry point + SUPPORTED_BANKS tuple
    models.py            # Pydantic models: Money, TransactionAlert, ParsedEmail
    exceptions.py        # ParseError, UnsupportedEmailTypeError
    utils.py             # Shared helpers: parse_date, parse_amount, parse_money,
                         #   extract_table_pairs, normalize_key, normalize_whitespace
    parsers/
        base.py          # BaseEmailParser ABC + parse_with_parsers() dispatcher
        axis.py          # Axis Bank
        equitas.py       # Equitas Small Finance Bank
        hdfc.py          # HDFC Bank
        hsbc.py          # HSBC
        icici.py         # ICICI Bank
        idfc.py          # IDFC FIRST Bank
        indusind.py      # IndusInd Bank
        kotak.py         # Kotak Bank / Kotak811
        onecard.py       # OneCard (BOBCARD)
        sbi.py           # SBI Card
        slice.py         # Slice savings bank
        uboi.py          # Union Bank of India
tests/
    test_new_parsers.py  # pytest tests using synthetic HTML
data/
    *.eml                # Real anonymised email samples for manual testing
```

## How parsers work

### 1. Entry point: `parse_email(bank, html)`

`api.py` dynamically imports `bank_email_parser.parsers.<bank>` and calls its module-level `parse(html)` function. The bank identifier must be in `SUPPORTED_BANKS`.

### 2. Parser modules

Each parser module follows this pattern:

```python
# parsers/example.py
"""Example Bank email parsers.

Supported email types:
- example_cc_alert: Credit card spend alert
"""
from bank_email_parser.parsers.base import BaseEmailParser, parse_with_parsers

class ExampleCcAlertParser(BaseEmailParser):
    bank = "example"
    email_type = "example_cc_alert"

    _pattern = re.compile(r"...")

    def parse(self, html: str) -> ParsedEmail:
        soup, text = self.prepare_html(html)
        if not (match := self._pattern.search(text)):
            raise ParseError("Could not parse ...")
        # ... extract fields and return ParsedEmail(...)

_PARSERS = (
    ExampleCcAlertParser(),
)

def parse(html: str) -> ParsedEmail:
    return parse_with_parsers("example", html, _PARSERS)
```

### 3. `BaseEmailParser`

Abstract base class (`parsers/base.py`) with two required class attributes and one abstract method:

- `bank: str` — bank identifier (e.g. `"icici"`)
- `email_type: str` — email type slug (e.g. `"icici_cc_transaction_alert"`)
- `parse(self, html: str) -> ParsedEmail` — raise `ParseError` if the email does not match

### 4. `parse_with_parsers()` dispatcher

Tries each parser in `_PARSERS` in order. Returns the first successful result. If every parser raises `ParseError` or `NotImplementedError`, re-raises `ParseError` with a combined error message listing all parsers that were tried.

Stubs (`raise NotImplementedError(...)`) are used for email types where no sample email is yet available. They are included in `_PARSERS` so their `email_type` appears in error messages.

## Key patterns

### Regex-based extraction (most parsers)

Most parsers flatten the HTML to plain text with `normalize_whitespace(soup.get_text(...))` and then run one or more compiled `re.compile(...)` patterns against it. Named groups (`(?P<name>...)`) are used for clarity.

`normalize_whitespace()` (in `utils.py`) replaces `\xa0` (non-breaking space) and `\u200c` (zero-width non-joiner) with regular spaces, then collapses all whitespace runs to a single space.

### HTML table extraction (`extract_table_pairs`)

For emails with 2-column `<table>` layouts, `extract_table_pairs(soup)` in `utils.py` walks every `<tr>`, collects pairs of `<td>` cells, normalizes the left cell as a key via `normalize_key()`, and returns a `dict[str, str]`. Pass `expected_keys=` to filter to only the keys you care about.

`normalize_key()` strips punctuation (colons, asterisks, etc.), lowercases, and collapses whitespace. Example: `"Transaction Date:"` → `"transaction date"`.

### Label/value div extraction (Axis Bank)

Axis emails use a card-layout with `<div style="color:#777777">` (labels) and `<div style="color:#333333">` (values). `axis.py` walks label divs, maps them via `_FIELD_MAP`, and reads the immediately following sibling div as the value.

### `<ul><li>` list extraction (Union Bank)

`uboi.py` locates a `<h3>Transaction Details:</h3>` heading, then reads `<li>` elements from the following `<ul>`, splitting each on ` - ` to get key/value pairs.

### Amount parsing

`parse_amount(raw)` in `utils.py` strips `₹`, `Rs.`, `Rs`, commas, `\xa0`, and `\u200c`, then constructs a `Decimal`. Returns `None` on failure. Use `parse_money(raw)` to get a `Money` object directly.

### Date parsing

`parse_date(date_str)` in `utils.py` tries a fixed list of common Indian bank date formats in order (e.g. `%d-%b-%y`, `%d/%m/%Y`, `%d %b %Y`, etc.) and returns a `datetime.date` or `None`.

Several parsers implement their own `_parse_*_datetime()` helpers when they also need to extract a time component, combining the date and time strings before parsing.

## Running tests

```bash
uv run pytest
```

## Testing a parser against a real .eml file

```python
import email, quopri
from bank_email_parser import parse_email

raw = open("data/slice_upi_credit.eml", "rb").read()
msg = email.message_from_bytes(raw)

# Find the HTML part
html = None
for part in msg.walk():
    if part.get_content_type() == "text/html":
        payload = part.get_payload(decode=True)
        html = payload.decode(part.get_content_charset() or "utf-8")
        break

result = parse_email("slice", html)
print(result.model_dump_json(indent=2))
```

## Adding a new bank

1. Create `src/bank_email_parser/parsers/{bank}.py` with a module docstring listing email types.
2. Write one `BaseEmailParser` subclass per email format. Set `bank` and `email_type` as class attributes. Implement `parse(self, html)`.
3. Add a module-level `_PARSERS` tuple and a `parse(html)` function calling `parse_with_parsers`.
4. Add the bank ID string to `SUPPORTED_BANKS` in `src/bank_email_parser/api.py`.
5. Add tests in `tests/` using synthetic HTML that matches the real email format.
6. If you have a real `.eml` file, add it (anonymised) to `data/`.

## Cross-project rules

- **Don't rename `email_type` values**: `bank-email-fetcher` stores them in its DB and uses them in `seed.py` fetch rules. Renaming is a breaking change.
- **When adding a new bank**: Also add fetch rules in `bank-email-fetcher/seed.py` (FROM address, SUBJECT pattern).
- **Parser ordering**: Within `_PARSERS`, specific parsers before broad ones, stubs last. `parse_with_parsers()` uses first-match semantics.

## Known stubs

- `axis_neft_alert`: Intentional stub — no sample email available.
- `icici_cc_reversal`: Intentional stub.

These exist in `_PARSERS` so their `email_type` shows up in error messages.

## Caller responsibilities

- **Caller must know the bank**: `parse_email(bank, html)` requires the bank identifier. No auto-detection.
- **Caller must extract HTML from MIME**: Library only accepts a plain HTML string.
- **Library is pure and stateless**: No DB, no email fetching, no side effects.
