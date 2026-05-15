import aiohttp
from bring_api import Bring
from bring_api.exceptions import BringAuthException, BringRequestException

from ..models import ActionResult, Item, ShoppingList, ShoppingListItems


class BringClientError(Exception):
    pass


async def _make_client(email: str, password: str) -> tuple[Bring, aiohttp.ClientSession]:
    session = aiohttp.ClientSession()
    bring = Bring(session, email, password)
    try:
        await bring.login()
    except BringAuthException as e:
        await session.close()
        raise BringClientError(f"Authentication failed: {e}") from e
    except BringRequestException as e:
        await session.close()
        raise BringClientError(f"API error: {e}") from e
    return bring, session


async def fetch_lists(email: str, password: str) -> list[ShoppingList]:
    bring, session = await _make_client(email, password)
    try:
        response = await bring.load_lists()
        return [
            ShoppingList(uuid=lst.listUuid, name=lst.name, theme=lst.theme)
            for lst in response.lists
        ]
    except BringRequestException as e:
        raise BringClientError(f"API error: {e}") from e
    finally:
        await session.close()


async def _resolve_list(bring: Bring, list_ref: str) -> ShoppingList:
    """Löst eine List-Referenz (UUID oder Name) zu einer ShoppingList auf."""
    response = await bring.load_lists()
    # Direkte UUID-Übereinstimmung
    for lst in response.lists:
        if lst.listUuid == list_ref:
            return ShoppingList(uuid=lst.listUuid, name=lst.name, theme=lst.theme)
    # Name-Suche (case-insensitive)
    matches = [lst for lst in response.lists if lst.name.lower() == list_ref.lower()]
    if len(matches) == 1:
        lst = matches[0]
        return ShoppingList(uuid=lst.listUuid, name=lst.name, theme=lst.theme)
    if len(matches) > 1:
        ids = ", ".join(lst.listUuid for lst in matches)
        raise BringClientError(
            f"Multiple lists named {list_ref!r} found. Please use the UUID: {ids}"
        )
    raise BringClientError(f"List {list_ref!r} not found.")


async def fetch_list_items(
    email: str, password: str, list_ref: str, include_recent: bool = False
) -> ShoppingListItems:
    bring, session = await _make_client(email, password)
    try:
        lst = await _resolve_list(bring, list_ref)
        response = await bring.get_list(lst.uuid)
        purchase = [
            Item(name=p.itemId, specification=p.specification) for p in response.items.purchase
        ]
        recently = (
            [Item(name=p.itemId, specification=p.specification) for p in response.items.recently]
            if include_recent
            else []
        )
        return ShoppingListItems(uuid=lst.uuid, name=lst.name, purchase=purchase, recently=recently)
    except BringRequestException as e:
        raise BringClientError(f"API error: {e}") from e
    finally:
        await session.close()


async def add_item(
    email: str, password: str, list_ref: str, item_name: str, specification: str = ""
) -> ActionResult:
    bring, session = await _make_client(email, password)
    try:
        lst = await _resolve_list(bring, list_ref)
        await bring.save_item(lst.uuid, item_name, specification)
        return ActionResult(status="ok", item=item_name, list=lst.name)
    except BringRequestException as e:
        raise BringClientError(f"API error: {e}") from e
    finally:
        await session.close()


async def add_items_bulk(
    email: str, password: str, list_ref: str, items: list[dict[str, str]]
) -> ActionResult:
    bring, session = await _make_client(email, password)
    try:
        lst = await _resolve_list(bring, list_ref)
        for item in items:
            await bring.save_item(lst.uuid, item["name"], item.get("specification", ""))
        names = ", ".join(i["name"] for i in items)
        return ActionResult(status="ok", item=names, list=lst.name)
    except BringRequestException as e:
        raise BringClientError(f"API error: {e}") from e
    finally:
        await session.close()


async def remove_item(email: str, password: str, list_ref: str, item_name: str) -> ActionResult:
    bring, session = await _make_client(email, password)
    try:
        lst = await _resolve_list(bring, list_ref)
        await bring.remove_item(lst.uuid, item_name)
        return ActionResult(status="ok", item=item_name, list=lst.name)
    except BringRequestException as e:
        raise BringClientError(f"API error: {e}") from e
    finally:
        await session.close()


async def check_off_item(email: str, password: str, list_ref: str, item_name: str) -> ActionResult:
    bring, session = await _make_client(email, password)
    try:
        lst = await _resolve_list(bring, list_ref)
        await bring.complete_item(lst.uuid, item_name)
        return ActionResult(status="ok", item=item_name, list=lst.name)
    except BringRequestException as e:
        raise BringClientError(f"API error: {e}") from e
    finally:
        await session.close()
