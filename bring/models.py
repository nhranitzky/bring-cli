from pydantic import BaseModel


class ShoppingList(BaseModel):
    uuid: str
    name: str
    theme: str


class Item(BaseModel):
    name: str
    specification: str = ""


class ShoppingListItems(BaseModel):
    uuid: str
    name: str
    purchase: list[Item]
    recently: list[Item]


class ActionResult(BaseModel):
    status: str
    item: str
    list: str
