# pylint: disable=unused-argument

from datetime import timedelta

from aiohttp import ClientSession
from applifting_exercise.database import Database
from freezegun.api import FrozenDateTimeFactory


async def test_basic_info(test_web_server: None, api_url_base: str) -> None:
    async with ClientSession() as session:
        async with session.get(f"{api_url_base}") as response:
            assert response.status == 200


async def test_status(test_web_server: None, api_url_base: str) -> None:
    async with ClientSession() as session:
        async with session.get(f"{api_url_base}/status") as response:
            assert response.status == 200


async def test_invalid_token(test_web_server: None, api_url_v1: str) -> None:
    async with ClientSession() as session:
        async with session.post(
            f"{api_url_v1}/products",
            headers={"Authorization": "Bearer INVALID_TOKEN"},
        ) as response:
            assert response.status == 401


async def test_expired_token(
    prepared_db: Database, test_web_server: None, api_url_v1: str, freezer: FrozenDateTimeFactory
) -> None:
    json_data = {"username": "Username", "password": "TestPWD123456"}

    async with ClientSession() as session:
        async with session.post(f"{api_url_v1}/login", json=json_data) as response:
            assert response.status == 200
            test_res_login = await response.json()

        token = test_res_login["token"]
        freezer.tick(timedelta(hours=2))

        async with session.post(
            f"{api_url_v1}/products",
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            assert response.status == 401


async def test_invalid_body(
    prepared_db: Database, test_web_server: None, api_url_v1: str, jwt_testing_token: str
) -> None:

    async with ClientSession() as session:
        async with session.post(
            f"{api_url_v1}/products",
            data=b"TEST",
            headers={"Authorization": f"Bearer {jwt_testing_token}"},
        ) as response:
            assert response.status == 400
