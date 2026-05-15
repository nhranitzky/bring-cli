import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from bring.cli import app
from bring.models import ActionResult, Item, ShoppingList, ShoppingListItems

runner = CliRunner()

LISTS = [
    ShoppingList(uuid="uuid-1", name="Wocheneinkauf", theme="blue"),
    ShoppingList(uuid="uuid-2", name="Drogerie", theme="green"),
]
ITEMS = ShoppingListItems(
    uuid="uuid-1",
    name="Wocheneinkauf",
    purchase=[Item(name="Milch", specification="2l"), Item(name="Butter")],
    recently=[Item(name="Eier")],
)


@pytest.fixture(autouse=True)
def set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRING_EMAIL", "test@example.com")
    monkeypatch.setenv("BRING_PASSWORD", "secret")


def test_lists_text() -> None:
    with patch("bring.cli.fetch_lists", new_callable=AsyncMock, return_value=LISTS):
        result = runner.invoke(app, ["lists"])
    assert result.exit_code == 0
    assert "Wocheneinkauf" in result.output


def test_lists_json() -> None:
    with patch("bring.cli.fetch_lists", new_callable=AsyncMock, return_value=LISTS):
        result = runner.invoke(app, ["lists", "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["name"] == "Wocheneinkauf"


def test_show_text() -> None:
    items_no_recent = ShoppingListItems(
        uuid="uuid-1",
        name="Wocheneinkauf",
        purchase=[Item(name="Milch", specification="2l"), Item(name="Butter")],
        recently=[],
    )
    with patch(
        "bring.cli.fetch_list_items", new_callable=AsyncMock, return_value=items_no_recent
    ):
        result = runner.invoke(app, ["show", "Wocheneinkauf"])
    assert result.exit_code == 0
    assert "Milch" in result.output
    assert "Eier" not in result.output


def test_show_include_recent() -> None:
    with patch("bring.cli.fetch_list_items", new_callable=AsyncMock, return_value=ITEMS):
        result = runner.invoke(app, ["show", "Wocheneinkauf", "--include-recent"])
    assert result.exit_code == 0
    assert "Eier" in result.output


def test_show_uses_bring_list_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRING_LIST", "Wocheneinkauf")
    with patch("bring.cli.fetch_list_items", new_callable=AsyncMock, return_value=ITEMS):
        result = runner.invoke(app, ["show"])
    assert result.exit_code == 0


def test_show_no_list_no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BRING_LIST", raising=False)
    result = runner.invoke(app, ["show"])
    assert result.exit_code == 1


def test_add_item() -> None:
    action = ActionResult(status="ok", item="Milch", list="Wocheneinkauf")
    with patch("bring.cli.add_item", new_callable=AsyncMock, return_value=action):
        result = runner.invoke(app, ["add", "Wocheneinkauf", "Milch", "--spec", "2l"])
    assert result.exit_code == 0
    assert "Milch" in result.output


def test_add_item_with_bring_list_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRING_LIST", "Wocheneinkauf")
    action = ActionResult(status="ok", item="Tomaten", list="Wocheneinkauf")
    with patch("bring.cli.add_item", new_callable=AsyncMock, return_value=action):
        result = runner.invoke(app, ["add", "Tomaten"])
    assert result.exit_code == 0
    assert "Tomaten" in result.output


def test_add_items_from_file(tmp_path: Path) -> None:
    items_file = tmp_path / "items.json"
    items_file.write_text(
        json.dumps([{"name": "Milch", "specification": "2l"}, {"name": "Butter"}])
    )
    action = ActionResult(status="ok", item="Milch, Butter", list="Wocheneinkauf")
    with patch("bring.cli.add_items_bulk", new_callable=AsyncMock, return_value=action):
        result = runner.invoke(app, ["add-items", "Wocheneinkauf", str(items_file)])
    assert result.exit_code == 0


def test_add_items_invalid_json(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not json")
    result = runner.invoke(app, ["add-items", "Wocheneinkauf", str(bad_file)])
    assert result.exit_code == 1


def test_remove_item() -> None:
    action = ActionResult(status="ok", item="Milch", list="Wocheneinkauf")
    with patch("bring.cli.remove_item", new_callable=AsyncMock, return_value=action):
        result = runner.invoke(app, ["remove", "Wocheneinkauf", "Milch"])
    assert result.exit_code == 0


def test_check_off_item() -> None:
    action = ActionResult(status="ok", item="Milch", list="Wocheneinkauf")
    with patch("bring.cli.check_off_item", new_callable=AsyncMock, return_value=action):
        result = runner.invoke(app, ["check-off", "Wocheneinkauf", "Milch"])
    assert result.exit_code == 0


def test_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BRING_EMAIL")
    result = runner.invoke(app, ["lists"])
    assert result.exit_code == 1
