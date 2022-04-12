import asyncio
import sys
from asyncio.events import AbstractEventLoop
from typing import AsyncGenerator, Generator

import pytest
from applifting_exercise.web import WebServer


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
async def test_web_server() -> AsyncGenerator[None, None]:
    web_server = WebServer()
    await web_server.start_web_server()
    yield
    await web_server.aclose()
