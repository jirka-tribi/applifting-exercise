# pylint: disable=unused-argument

from aiohttp import ClientSession


async def test_basic_info(test_web_server: None, api_url_base: str) -> None:
    async with ClientSession() as session:
        async with session.get(f"{api_url_base}") as response:
            assert response.status == 200


async def test_status(test_web_server: None, api_url_base: str) -> None:
    async with ClientSession() as session:
        async with session.get(f"{api_url_base}/status") as response:
            assert response.status == 200
