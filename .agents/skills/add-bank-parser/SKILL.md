---
name: add-bank-parser
description: Add a new bank email parser or add a new email type to an existing bank. Use when adding support for parsing transaction alert or statement emails from a bank.
---

# Add or Update a Bank Email Parser

**This skill is interactive.** It requires running Python to extract and test against email HTML. Do not run this in the background. If you need tool permissions, ask for them.

Arguments: `$ARGUMENTS` — bank slug and sample email (raw .eml path or HTML body).

## Step 1: Study the codebase

Read these files:
- `AGENTS.md` — architecture, parser interface, key patterns
- `src/bank_email_parser/models.py` — output schema (see Output Schema below)
- `src/bank_email_parser/parsers/base.py` — `BaseEmailParser` interface and `parse_with_parsers()` dispatcher
- At least one existing parser — a simple one for new banks, a multi-type one for adding email types
- `src/bank_email_parser/api.py` — `SUPPORTED_BANKS`, `parse_email()`

## Step 2: Extract and examine the email HTML

**MANDATORY. Do not write any parser code before completing this step.**

If given a `.eml` file, run code to extract the HTML body:

```python
import email
with open("<path>", "rb") as f:
    msg = email.message_from_bytes(f.read())
for part in msg.walk():
    if part.get_content_type() == "text/html":
        html = part.get_payload(decode=True).decode()
        print(html[:3000])
        break
```

From the HTML, identify:
- What data is present (amount, direction, date, time, counterparty, account/card mask, reference number, channel, balance)
- How it's structured (HTML table, key-value `<li>` list, prose text, structured `<span>`/`<td>` elements)
- Unique markers that identify this email type (specific phrases, class names, structure)
- For statement emails: password hint text

## Step 3: Write the parser

**New bank** — create `src/bank_email_parser/parsers/{bank}.py`:
- One `BaseEmailParser` subclass per email type
- Set `bank` and `email_type` class attributes (`email_type` follows `{bank}_{description}` convention)
- Implement `parse(self, html) -> ParsedEmail` — use `self.prepare_html(html)` to get `(soup, normalized_text)`
- Raise `ParseError` if the email doesn't match (never return None)
- Create `_PARSERS` tuple — specific parsers first, broad ones last, stubs at end
- Create module-level `parse(html)` function calling `parse_with_parsers()`
- Add bank to `SUPPORTED_BANKS` in `api.py`

**New email type for existing bank** — add a new `BaseEmailParser` subclass to the bank's file, add it to `_PARSERS` in the right position.

**Statement email parser** — add a `{Bank}StatementEmailParser` class (last in `_PARSERS`, broadest match) that:
- Guards strictly: check for both `"statement"` AND (`"password"` / `"attached"` / bank-specific markers) to avoid false-matching transaction alert footers
- Returns `ParsedEmail(transaction=None, password_hint="...")` with a hardcoded hint describing the bank's password scheme (e.g., `"Date of birth in DDMMYYYY format"`, `"First 4 characters of name (uppercase) + DDMM of birth"`, `"Customer ID as the password"`)

## Step 4: Test and iterate

Test via `uv run python -c "..."`:

```python
from bank_email_parser.api import parse_email
result = parse_email("{bank}", html_string)
print(result.model_dump())
```

Check all fields: `email_type`, `bank`, `transaction` (direction, amount, date, counterparty, channel, masks, reference), and `password_hint` for statement emails. Test edge cases.

This is iterative — if parsing fails or fields are wrong, examine the HTML more closely, fix the parser, re-test.

## Output Schema

`ParsedEmail` (from `models.py`):

```
ParsedEmail:
  email_type: str                              # "{bank}_{type}" e.g. "hdfc_upi_alert"
  bank: str
  transaction: TransactionAlert | None         # None for statement emails
  password_hint: str | None                    # for statement emails with encrypted PDFs
```

`TransactionAlert`:
```
TransactionAlert:
  direction: "debit" | "credit" | "declined"
  amount: Money                                # {amount: Decimal, currency: "INR"}
  transaction_date: date | None
  transaction_time: time | None
  counterparty: str | None
  balance: Money | None
  reference_number: str | None
  account_mask: str | None                     # last 4 digits of account
  card_mask: str | None                        # last 4 digits of card
  channel: str | None                          # upi, neft, imps, rtgs, card, atm, netbanking
```

## Gotchas

- **Raise `ParseError`, never return None.** The dispatcher catches it and tries the next parser.
- **`prepare_html()` caches per dispatch.** Thread-safe via thread-local storage. Call freely.
- **Parser ordering in `_PARSERS` matters.** Specific before broad. Stubs last.
- **Parser stubs.** For known-but-unimplemented types, raise `ParserStubError` to prevent wrong-parser fallthrough.
- **Amount parsing.** Use `Decimal`. Indian lakhs grouping: "1,52,581.54". Strip ₹/Rs./INR.
- **Date parsing.** Normalize to `datetime.date`. Banks vary: DD-MM-YYYY, DD MMM YYYY, DD/MM/YY.
- **Channel values.** Lowercase: "upi", "neft", "imps", "rtgs", "card", "atm", "netbanking".
- **HTML extraction.** BeautifulSoup `find()` with text regex for specific elements, `find_all("td")` for tables, regex on normalized text for prose. Check existing parsers for examples.

## Self-improvement

If you discover new patterns, email formats, or extraction techniques, update this skill.
