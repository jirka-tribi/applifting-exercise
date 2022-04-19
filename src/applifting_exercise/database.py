import logging
from importlib import resources
from typing import Any, Dict, Optional

import asyncpg
from asyncpg.exceptions import CannotConnectNowError, ConnectionDoesNotExistError

from .models import Product, User

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
                        users (username, hashed_pwd)
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
            user_record = await con.fetchrow(
                """
                    SELECT
                        id, username, hashed_pwd
                    FROM
                        users
                    WHERE
                        username = $1
                """,
                username,
            )

        return User(**user_record) if user_record else None

    async def create_product(self, name: str, description: str) -> int:
        async with self.pg_pool.acquire() as con:
            product_id = await con.fetchval(
                """
                    INSERT INTO
                        products ("name", description)
                    VALUES
                        ($1, $2)
                    RETURNING id
                """,
                name,
                description,
            )

        return int(product_id)

    async def get_product(self, product_id: int) -> Optional[Product]:
        async with self.pg_pool.acquire() as con:
            product_record = await con.fetchrow(
                """
                    SELECT
                        id, "name", description
                    FROM
                        products
                    WHERE
                        id = $1
                """,
                product_id,
            )

        return Product(**product_record) if product_record else None

    async def update_product(self, product: Product) -> str:
        async with self.pg_pool.acquire() as con:
            updated = await con.execute(
                """
                    UPDATE
                        products
                    SET
                        "name" = $2, description = $3
                    WHERE
                        id = $1
                """,
                product.id,
                product.name,
                product.description,
            )

        return str(updated)

    async def delete_product(self, product_id: int) -> str:
        async with self.pg_pool.acquire() as con:
            deleted = await con.execute(
                """
                    DELETE FROM
                        products
                    WHERE
                        id = $1
                """,
                product_id,
            )

        return str(deleted)

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
