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

    id: int
    username: str
    hashed_pwd: bytes
