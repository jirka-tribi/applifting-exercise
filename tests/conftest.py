import asyncio
import sys
from asyncio.events import AbstractEventLoop
from typing import AsyncGenerator, Generator

import asyncpg
import pytest
import pytest_docker
import tenacity
from applifting_exercise.core import Core
from applifting_exercise.database import Database
from applifting_exercise.web import WebServer
from asyncpg.exceptions import CannotConnectNowError, ConnectionDoesNotExistError
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_fixed


@pytest.fixture(scope="session")
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    # avoid RuntimeError('Event loop is closed') on windows machines
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def api_url_base() -> str:
    return "http://localhost:8080"


@pytest.fixture(scope="session")
def postgres_dsn(docker_services: pytest_docker.plugin.Services) -> str:
    host = "127.0.0.1"
    port = docker_services.port_for("postgres", 5432)
    username = password = "postgres"
    database = "postgres"
    return f"postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=disable"


@pytest.fixture(scope="session")
async def test_db(postgres_dsn: str) -> AsyncGenerator[Database, None]:
    @tenacity.retry(
        stop=stop_after_delay(60),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(
            (
                ConnectionDoesNotExistError,
                CannotConnectNowError,
                ConnectionRefusedError,
            )
        ),
    )
    async def connect_pg_pool() -> asyncpg.pool.Pool:
        return await asyncpg.create_pool(dsn=postgres_dsn)

    pg_pool = await connect_pg_pool()
    database = Database(pg_pool)
    await database.ensure_schema()
    yield database
    await database.aclose()


@pytest.fixture(scope="session")
async def test_web_server(test_db: Database) -> AsyncGenerator[None, None]:

    core = Core(db=test_db)
    web_server = WebServer(core)
    await web_server.start_web_server()
    yield
    await web_server.aclose()
