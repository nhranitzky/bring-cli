import asyncio
import json
import os
from pathlib import Path
from typing import Annotated

import typer

from .core.bring_client import (
    BringClientError,
    add_item,
    add_items_bulk,
    check_off_item,
    fetch_list_items,
    fetch_lists,
    remove_item,
)
from .output import OutputFormat, render, render_error

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)

OutputOption = Annotated[
    OutputFormat,
    typer.Option("--output", "-o", help="Ausgabeformat: text oder json"),
]


def _credentials() -> tuple[str, str]:
    email = os.environ.get("BRING_EMAIL", "")
    password = os.environ.get("BRING_PASSWORD", "")
    if not email or not password:
        typer.echo("Error: BRING_EMAIL and BRING_PASSWORD must be set.", err=True)
        raise typer.Exit(1)
    return email, password


def _list_ref(list_arg: str | None) -> str:
    if list_arg:
        return list_arg
    default = os.environ.get("BRING_LIST", "")
    if not default:
        typer.echo("Error: No list argument provided and BRING_LIST is not set.", err=True)
        raise typer.Exit(1)
    return default


def _resolve_list_and_item(list_arg: str | None, item_arg: str) -> tuple[str | None, str]:
    """Verschiebt list_arg → item_arg wenn BRING_LIST gesetzt ist und nur ein Argument kam."""
    if not item_arg and list_arg and os.environ.get("BRING_LIST"):
        return None, list_arg
    return list_arg, item_arg


@app.command()
def lists(output: OutputOption = OutputFormat.text) -> None:
    """Alle Einkaufslisten anzeigen."""
    email, password = _credentials()
    try:
        result = asyncio.run(fetch_lists(email, password))
        render(result, output)
    except BringClientError as e:
        render_error(str(e), output)


@app.command()
def show(
    list_ref: Annotated[str | None, typer.Argument(help="Listen-ID oder Name")] = None,
    include_recent: Annotated[
        bool, typer.Option("--include-recent", help="Zuletzt gekaufte Items anzeigen")
    ] = False,
    output: OutputOption = OutputFormat.text,
) -> None:
    """Items einer Einkaufsliste anzeigen."""
    email, password = _credentials()
    ref = _list_ref(list_ref)
    try:
        result = asyncio.run(fetch_list_items(email, password, ref, include_recent))
        render(result, output)
    except BringClientError as e:
        render_error(str(e), output)


@app.command()
def add(
    list_ref: Annotated[str | None, typer.Argument(help="Listen-ID oder Name")] = None,
    item: Annotated[str, typer.Argument(help="Name des Items")] = "",
    spec: Annotated[str, typer.Option("--spec", "-s", help="Spezifikation (z.B. '2l')")] = "",
    output: OutputOption = OutputFormat.text,
) -> None:
    """Item zu einer Einkaufsliste hinzufügen."""
    email, password = _credentials()
    list_ref, item = _resolve_list_and_item(list_ref, item)
    ref = _list_ref(list_ref)
    if not item:
        typer.echo("Error: Item name must not be empty.", err=True)
        raise typer.Exit(1)
    try:
        result = asyncio.run(add_item(email, password, ref, item, spec))
        render(result, output)
    except BringClientError as e:
        render_error(str(e), output)


@app.command("add-items")
def add_items(
    list_ref: Annotated[str | None, typer.Argument(help="Listen-ID oder Name")] = None,
    file: Annotated[Path, typer.Argument(help="Pfad zur JSON-Datei")] = Path(""),
    output: OutputOption = OutputFormat.text,
) -> None:
    """Mehrere Items aus einer JSON-Datei hinzufügen."""
    email, password = _credentials()
    ref = _list_ref(list_ref)
    if not file or not file.exists():
        typer.echo(f"Error: File not found: {file}", err=True)
        raise typer.Exit(1)
    try:
        raw = json.loads(file.read_text())
        if not isinstance(raw, list):
            raise ValueError("JSON muss eine Liste sein.")
        items: list[dict[str, str]] = [
            {"name": entry["name"], "specification": entry.get("specification", "")}
            if isinstance(entry, dict)
            else {"name": str(entry), "specification": ""}
            for entry in raw
        ]
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        typer.echo(f"Error: Invalid JSON format: {e}", err=True)
        raise typer.Exit(1) from None
    try:
        result = asyncio.run(add_items_bulk(email, password, ref, items))
        render(result, output)
    except BringClientError as e:
        render_error(str(e), output)


@app.command()
def remove(
    list_ref: Annotated[str | None, typer.Argument(help="Listen-ID oder Name")] = None,
    item: Annotated[str, typer.Argument(help="Name des Items")] = "",
    output: OutputOption = OutputFormat.text,
) -> None:
    """Item aus einer Einkaufsliste entfernen."""
    email, password = _credentials()
    list_ref, item = _resolve_list_and_item(list_ref, item)
    ref = _list_ref(list_ref)
    if not item:
        typer.echo("Error: Item name must not be empty.", err=True)
        raise typer.Exit(1)
    try:
        result = asyncio.run(remove_item(email, password, ref, item))
        render(result, output)
    except BringClientError as e:
        render_error(str(e), output)


@app.command("check-off")
def check_off(
    list_ref: Annotated[str | None, typer.Argument(help="Listen-ID oder Name")] = None,
    item: Annotated[str, typer.Argument(help="Name des Items")] = "",
    output: OutputOption = OutputFormat.text,
) -> None:
    """Item als gekauft markieren (in 'Zuletzt' verschieben)."""
    email, password = _credentials()
    list_ref, item = _resolve_list_and_item(list_ref, item)
    ref = _list_ref(list_ref)
    if not item:
        typer.echo("Error: Item name must not be empty.", err=True)
        raise typer.Exit(1)
    try:
        result = asyncio.run(check_off_item(email, password, ref, item))
        render(result, output)
    except BringClientError as e:
        render_error(str(e), output)


def main() -> None:
    app(prog_name="bring-cli")
