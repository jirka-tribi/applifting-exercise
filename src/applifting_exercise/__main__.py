import asyncio
from importlib import resources
from typing import Any, Dict, Optional

from pyhocon import ConfigFactory

from .core import Core
from .database import Database
from .services import OffersService
from .web import WebServer


class App:
    def __init__(self) -> None:
        self.db: Optional[Database] = None
        self.core: Optional[Core] = None
        self.web_server: Optional[WebServer] = None
        self.offers_service: Optional[OffersService] = None

        # Load config.conf file with all required configurations fields
        with resources.path(__package__, "config.conf") as config_path:
            self.config: Dict[str, Any] = ConfigFactory.parse_file(config_path)

    async def setup(self) -> None:
        self.db = await Database.async_init(self.config["postgres"])
        await self.db.ensure_schema()

        # Call offers service and store header with auth token for other calls
        self.offers_service = await OffersService.async_init(self.config["offers"])

        self.core = Core(
            offers_service=self.offers_service,
            db=self.db,
            app_internal_token=self.config["general"]["app_internal_token"],
        )

        self.web_server = WebServer(self.core, self.config["web"]["port"])

    async def run(self) -> None:
        assert self.web_server is not None
        assert self.core is not None

        await asyncio.gather(self.web_server.start_web_server(), self.core.background_tasks())

    async def aclose(self) -> None:
        if self.web_server:
            await self.web_server.aclose()

        if self.db:
            await self.db.aclose()

        if self.offers_service:
            await self.offers_service.aclose()


def main() -> None:
    app = App()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.setup())

    try:
        loop.run_until_complete(app.run())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(app.aclose())
        loop.close()
