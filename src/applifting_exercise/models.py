from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Union

from schema import And, Schema, Use

USER_REQUEST_SCHEMA = Schema(
    {
        "username": And(str, lambda s: 3 < len(s.strip()) < 100),
        "password": And(str, lambda s: 10 < len(s.strip()) < 100),
    }
)


@dataclass
class User:
    __slots__ = ["id", "username", "hashed_pwd"]

    id: int  # pylint: disable=invalid-name
    username: str
    hashed_pwd: bytes


PRODUCT_SCHEMA = Schema(
    {
        "name": And(str, lambda s: 3 < len(s.strip()) < 100),
        "description": str,
    }
)


@dataclass
class Product:
    __slots__ = ["id", "name", "description"]

    id: int  # pylint: disable=invalid-name
    name: str
    description: str


@dataclass
class Offer:
    __slots__ = ["id", "product_id", "price", "items_in_stock", "created_at"]

    id: int  # pylint: disable=invalid-name
    product_id: int
    price: int
    items_in_stock: int
    created_at: datetime

    @property
    def for_api(self) -> Dict[str, Union[str, int]]:
        return {"id": self.product_id, "price": self.price, "items_in_stock": self.items_in_stock}


PRICES_FROM_TO_SCHEMA = Schema(
    {
        "from_date": Use(datetime.fromisoformat),
        "to_date": Use(datetime.fromisoformat),
    }
)


@dataclass
class Price:
    __slots__ = ["value", "created_at"]

    value: int
    created_at: datetime
