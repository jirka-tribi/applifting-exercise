import logging
from importlib import resources
from typing import Any, Dict

import asyncpg
from asyncpg.exceptions import CannotConnectNowError, ConnectionDoesNotExistError

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
