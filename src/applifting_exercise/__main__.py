import asyncio
from typing import Optional

from .database import Database
from .web import WebServer


class App:
    def __init__(self) -> None:
        self.database: Optional[Database] = None
        self.web_server: Optional[WebServer] = None

    async def setup(self) -> None:
        self.database = await Database.async_init()
        await self.database.ensure_schema()

        self.web_server = WebServer()

    async def run(self) -> None:
        assert self.web_server is not None
        await self.web_server.start_web_server()

    async def aclose(self) -> None:
        if self.web_server:
            await self.web_server.aclose()

        if self.database:
            await self.database.aclose()


def main() -> None:
    app = App()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.setup())

    try:
        loop.run_until_complete(app.run())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(app.aclose())
