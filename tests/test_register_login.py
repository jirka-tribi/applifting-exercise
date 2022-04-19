# pylint: disable=unused-argument

from typing import Dict

import pytest
from aiohttp import ClientSession
from jose import jwt

INVALID_JSON_DATA = [
    {"username": "Username", "password": ""},
    {"username": "", "password": "TestPWD123456"},
    {"username": "", "password": "123"},
    {"invalid_key": "Test", "password": "TestPWD123456"},
    {"username": "Test", "invalid_key": "TestPWD123456"},
    {},
]


@pytest.mark.parametrize("invalid_json_data", INVALID_JSON_DATA)
async def test_invalid_input_data(
    test_web_server: None, api_url_v1: str, invalid_json_data: Dict[str, str]
) -> None:

    # All invalid input data should return 400
    async with ClientSession() as session:
        async with session.post(f"{api_url_v1}/register", json=invalid_json_data) as response:
            assert response.status == 400

        async with session.post(f"{api_url_v1}/login", json=invalid_json_data) as response:
            assert response.status == 400


async def test_incorrect_username_pwd(
    test_web_server: None, api_url_v1: str, drop_db_tables: None
) -> None:

    json_data = {"username": "Username", "password": "TestPWD123456"}
    json_data_incorrect_name = {"username": "Username_Incorrect", "password": "TestPWD123456"}
    json_data_incorrect_pwd = {
        "username": "Username",
        "password": "TestPWD123456Incorrect",
    }

    async with ClientSession() as session:
        # Register required username `Test_Correct`
        async with session.post(f"{api_url_v1}/register", json=json_data) as response:
            assert response.status == 200

        # Try register same username
        async with session.post(f"{api_url_v1}/register", json=json_data) as response:
            assert response.status == 401

        # Try login with incorrect (not registered) username
        async with session.post(f"{api_url_v1}/login", json=json_data_incorrect_name) as response:
            assert response.status == 401

        # Try login with incorrect password for registered username
        async with session.post(f"{api_url_v1}/login", json=json_data_incorrect_pwd) as response:
            assert response.status == 401


async def test_correct_register_login(
    test_web_server: None, api_url_v1: str, test_internal_token: str, drop_db_tables: None
) -> None:
    def validate_token(token: str) -> None:
        decoded_jwt_token = jwt.decode(token, test_internal_token, algorithms="HS256")
        assert decoded_jwt_token["id"] == 1
        assert decoded_jwt_token["username"] == "Username"

    json_data = {"username": "Username", "password": "TestPWD123456"}

    # Register and login with correct input data
    async with ClientSession() as session:
        async with session.post(f"{api_url_v1}/register", json=json_data) as response:
            assert response.status == 200
            test_res_register = await response.json()

        validate_token(test_res_register["token"])

        async with session.post(f"{api_url_v1}/login", json=json_data) as response:
            assert response.status == 200
            test_res_login = await response.json()

        validate_token(test_res_login["token"])
