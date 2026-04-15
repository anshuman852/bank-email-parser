"""Registry and import-stability tests."""

from importlib import import_module
from pathlib import Path

from bank_email_parser.api import SUPPORTED_BANKS
from bank_email_parser.parsers import PARSERS
from bank_email_parser.parsers.kotak import KotakParser


def test_registry_matches_parser_modules() -> None:
    parser_dir = Path(__file__).resolve().parents[1] / "bank_email_parser" / "parsers"
    filesystem_banks = {
        path.stem if path.is_file() else path.name
        for path in parser_dir.iterdir()
        if path.name not in {"__init__.py", "base.py", "__pycache__"}
        if not path.name.startswith("_")
    }

    assert tuple(PARSERS) == SUPPORTED_BANKS
    assert filesystem_banks == set(PARSERS)


def test_registry_entries_resolve_to_bank_dispatchers() -> None:
    for bank, parser_cls in PARSERS.items():
        module = import_module(f"bank_email_parser.parsers.{bank}")
        parser = parser_cls()

        assert parser.bank == bank
        assert getattr(module, parser_cls.__name__) is parser_cls
        assert callable(module.parse)
        assert callable(parser.parse)


def test_kotak_dispatcher_import_remains_stable() -> None:
    assert KotakParser is PARSERS["kotak"]
