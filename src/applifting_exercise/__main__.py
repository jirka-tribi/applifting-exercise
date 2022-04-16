import asyncio
from importlib import resources
from typing import Any, Dict, Optional

from pyhocon import ConfigFactory

from .core import Core
from .database import Database
from .web import WebServer


class App:
    def __init__(self) -> None:
        self.db: Optional[Database] = None
        self.core: Optional[Core] = None
        self.web_server: Optional[WebServer] = None

        # Load config.conf file with all required configurations fields
        with resources.path(__package__, "config.conf") as pg_config_path:
            self.config: Dict[str, Any] = ConfigFactory.parse_file(pg_config_path)

    async def setup(self) -> None:
        self.db = await Database.async_init(self.config["postgres"])
        await self.db.ensure_schema()

        self.core = Core(
            db=self.db, app_internal_token=self.config["general"]["app_internal_token"]
        )

        self.web_server = WebServer(self.core)

    async def run(self) -> None:
        assert self.web_server is not None
        await self.web_server.start_web_server()

    async def aclose(self) -> None:
        if self.web_server:
            await self.web_server.aclose()

        if self.db:
            await self.db.aclose()


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
        loop.close()
