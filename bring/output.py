import json
import sys
from collections.abc import Sequence
from enum import StrEnum

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

from .models import ActionResult, Item, ShoppingList, ShoppingListItems

console = Console()
err_console = Console(stderr=True)


class OutputFormat(StrEnum):
    text = "text"
    json = "json"


def render(data: BaseModel | Sequence[BaseModel], fmt: OutputFormat) -> None:
    if fmt == OutputFormat.json:
        if isinstance(data, Sequence):
            console.print_json(json.dumps([d.model_dump(mode="json") for d in data]))
        else:
            console.print_json(data.model_dump_json())
    else:
        _render_text(data)


def render_error(message: str, fmt: OutputFormat, code: str = "error") -> None:
    if fmt == OutputFormat.json:
        err_console.print_json(json.dumps({"error": message, "code": code}))
    else:
        err_console.print(f"[bold red]Error:[/bold red] {message}")
    sys.exit(1)


def _render_text(data: BaseModel | Sequence[BaseModel]) -> None:
    if isinstance(data, Sequence) and data and isinstance(data[0], ShoppingList):
        _render_lists([d for d in data if isinstance(d, ShoppingList)])
    elif isinstance(data, ShoppingListItems):
        _render_list_items(data)
    elif isinstance(data, ActionResult):
        console.print(f"[green]✓[/green] {data.item!r} in [bold]{data.list}[/bold]")
    else:
        console.print(data)


def _render_lists(lists: list[ShoppingList]) -> None:
    table = Table("UUID", "Name", "Theme", show_header=True, header_style="bold")
    for lst in lists:
        table.add_row(lst.uuid, lst.name, lst.theme)
    console.print(table)


def _render_list_items(data: ShoppingListItems) -> None:
    console.print(f"[bold]{data.name}[/bold]")
    if data.purchase:
        _render_items_section("To buy", data.purchase)
    if data.recently:
        _render_items_section("Recently bought", data.recently, dim=True)


def _render_items_section(title: str, items: list[Item], dim: bool = False) -> None:
    style = "dim" if dim else ""
    console.print(f"\n  [bold {style}]{title}[/bold {style}]")
    for item in items:
        spec = f"  [dim]{item.specification}[/dim]" if item.specification else ""
        console.print(f"  • {item.name}{spec}", style=style)
