# bank-email-parser

Parse Indian bank transaction alert emails into structured data.

## Install

```bash
uv sync
```

## Library usage

```python
from bank_email_parser import parse_email

result = parse_email("icici", html)
print(result.email_type)
print(result.transaction.amount.amount if result.transaction else None)
```

Public API remains:

- `parse_email`
- `SUPPORTED_BANKS`
- `ParsedEmail`
- `ParseError`, `UnsupportedEmailTypeError`

## CLI usage

Parse from a file:

```bash
uv run bank-email-parser sample.html --bank kotak
```

Parse from stdin:

```bash
cat sample.html | uv run bank-email-parser --bank hdfc
```

Output is JSON.

## Layout

```text
bank_email_parser/
├── api.py
├── cli.py
├── parsing/
│   ├── amounts.py
│   ├── dates.py
│   ├── html.py
│   └── keys.py
├── parsers/
│   ├── __init__.py   # explicit PARSERS registry
│   ├── base.py
│   ├── kotak/        # example multi-email-type bank subpackage
│   └── ...
└── utils.py          # compatibility re-exports
```

## Adding a parser

1. Add or update `bank_email_parser/parsers/{bank}.py` or `parsers/{bank}/`.
2. Expose a bank dispatcher class (`{Bank}Parser`).
3. Register it in `bank_email_parser/parsers/__init__.py`.
4. Reuse helpers from `bank_email_parser.parsing/`.
5. Add synthetic pytest coverage.

## Development

```bash
uv sync
uv run pytest -q
uv run ruff check
uv run ty check
```
