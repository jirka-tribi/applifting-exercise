from __future__ import annotations

from importlib import resources

import asyncpg
from pyhocon import ConfigFactory


class Database:
    def __init__(self, pg_pool: asyncpg.pool.Pool) -> None:
        self.pg_pool = pg_pool

    @classmethod
    async def async_init(cls) -> "Database":
        with resources.path(__package__, "database.conf") as pg_config_path:
            pg_config = ConfigFactory.parse_file(pg_config_path)

        pg_pool = await asyncpg.create_pool(**pg_config["postgres"])

        return cls(pg_pool)

    async def ensure_schema(self) -> None:
        async with self.pg_pool.acquire() as con:
            with resources.path(__package__, "database_schema.sql") as sql_schema_path:
                await con.execute(sql_schema_path.read_text())

    async def aclose(self) -> None:
        await self.pg_pool.close()
