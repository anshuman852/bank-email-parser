"""CLI entrypoint for parsing bank email HTML into JSON."""

from pathlib import Path

import click
import typer

from bank_email_parser.api import SUPPORTED_BANKS, parse_email
from bank_email_parser.exceptions import ParseError, UnsupportedEmailTypeError

app = typer.Typer(help="Parse a bank email HTML body and print normalized JSON.")


@app.callback(invoke_without_command=True)
def main(
    html_file: Path | None = typer.Argument(
        None,
        help="Path to an HTML file. Reads stdin when omitted.",
    ),
    bank: str = typer.Option(
        ...,
        "--bank",
        help="Bank identifier.",
        click_type=click.Choice(SUPPORTED_BANKS),
    ),
) -> None:
    """Parse an email body from a file or stdin."""
    if html_file is None:
        html = typer.get_text_stream("stdin").read()
    else:
        if not html_file.exists():
            raise typer.BadParameter(f"File not found: {html_file}")
        html = html_file.read_text(encoding="utf-8")

    try:
        result = parse_email(bank, html)
    except (UnsupportedEmailTypeError, ParseError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(result.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
