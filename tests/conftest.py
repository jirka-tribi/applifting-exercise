# pylint: disable=unused-argument, protected-access

import asyncio
import sys
from asyncio.events import AbstractEventLoop
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator

import asyncpg
import bcrypt
import pytest
import pytest_docker
import tenacity
from applifting_exercise.core import Core
from applifting_exercise.database import Database
from applifting_exercise.services import OffersService
from applifting_exercise.web import PREFIX_V1, WebServer
from asyncpg.exceptions import CannotConnectNowError, ConnectionDoesNotExistError
from jose import jwt
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
def api_url_v1(api_url_base: str) -> str:
    return f"{api_url_base}{PREFIX_V1}"


@pytest.fixture(scope="session")
def test_internal_token() -> str:
    return "TEST_INTERNAL_TOKEN"


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


@pytest.fixture(scope="function")
async def drop_db_tables(test_db: Database) -> None:
    async with test_db.pg_pool.acquire() as con:
        await con.execute("DROP TABLE users")
        await con.execute("DROP TABLE products")
        await con.execute("DROP TABLE offers")

    await test_db.ensure_schema()


@pytest.fixture(scope="function")
async def prepared_db(test_db: Database, drop_db_tables: None) -> AsyncGenerator[Database, None]:
    # Drop tables in testing DB and register one testing user (same as register endpoint)

    hashed_pwd = bcrypt.hashpw(b"TestPWD123456", bcrypt.gensalt())
    await test_db.register_user("Username", hashed_pwd)

    yield test_db


@pytest.fixture(scope="session")
def jwt_testing_token(test_internal_token: str) -> str:
    token = jwt.encode(
        {"id": 1, "username": "Username", "exp": datetime.utcnow() + timedelta(hours=1)},
        test_internal_token,
        algorithm="HS256",
    )

    return str(token)


@pytest.fixture(scope="session")
def offers_service() -> OffersService:
    offers_service = OffersService(
        {
            "offers_service_url": "https://test-offers.com/api/v1",
            "offers_service_concurrency": 5,
        }
    )
    offers_service._auth_header = {"Bearer": "TEST"}

    return offers_service


@pytest.fixture(scope="session")
async def test_web_server(
    offers_service: OffersService, test_db: Database, test_internal_token: str
) -> AsyncGenerator[None, None]:

    core = Core(offers_service=offers_service, db=test_db, app_internal_token=test_internal_token)
    web_server = WebServer(core)
    await web_server.start_web_server()
    yield
    await web_server.aclose()
    await offers_service.aclose()
