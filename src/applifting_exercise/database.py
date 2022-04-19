import logging
from importlib import resources
from typing import Any, Dict, Optional

import asyncpg
from asyncpg.exceptions import CannotConnectNowError, ConnectionDoesNotExistError

from .models import User

LOGGER = logging.getLogger(__name__)


class Database:
    def __init__(self, pg_pool: asyncpg.pool.Pool) -> None:
        self.pg_pool = pg_pool

    @classmethod
    async def async_init(cls, pg_config: Dict[str, Any]) -> "Database":
        pg_pool = await asyncpg.create_pool(**pg_config)

        return cls(pg_pool)

    async def ensure_schema(self) -> None:
        async with self.pg_pool.acquire() as con:
            with resources.path(__package__, "database_schema.sql") as sql_schema_path:
                await con.execute(sql_schema_path.read_text())

    async def register_user(self, username: str, hashed_pwd: bytes) -> Optional[int]:
        async with self.pg_pool.acquire() as con:
            user_id = await con.fetchval(
                """
                    INSERT INTO
                        users (username, password)
                    VALUES
                        ($1, $2)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """,
                username,
                hashed_pwd,
            )

        return int(user_id) if user_id else None

    async def get_user(self, username: str) -> Optional[User]:
        async with self.pg_pool.acquire() as con:
            record = await con.fetchrow(
                """
                    SELECT
                        id, username, password
                    FROM
                        users
                    WHERE
                        username = $1
                """,
                username,
            )

        return User(record["id"], record["username"], record["password"]) if record else None

    async def is_connected(self) -> bool:
        try:
            # Acquire and release connection from pool - liveness check
            async with self.pg_pool.acquire():
                pass
        except (ConnectionRefusedError, CannotConnectNowError, ConnectionDoesNotExistError):
            LOGGER.error("DB is not connected")
            return False

        return True

    async def aclose(self) -> None:
        await self.pg_pool.close()
