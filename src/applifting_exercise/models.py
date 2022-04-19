from dataclasses import dataclass

from schema import And, Schema

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
