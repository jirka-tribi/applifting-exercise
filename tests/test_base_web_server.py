from aiohttp import ClientSession


async def test_basic_info(test_web_server: None, api_url: str) -> None:
    # pylint: disable=unused-argument

    async with ClientSession() as session:
        async with session.get(f"{api_url}") as response:
            assert response.status == 200


async def test_status(test_web_server: None, api_url: str) -> None:
    # pylint: disable=unused-argument

    async with ClientSession() as session:
        async with session.get(f"{api_url}status") as response:
            assert response.status == 200
