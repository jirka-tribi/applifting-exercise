import asyncio
from importlib import resources
from typing import Any, Dict, Optional

from pyhocon import ConfigFactory

from .web_base import WebServerBase


class App:
    def __init__(self) -> None:
        self.web_server: Optional[WebServerBase] = None

        # Load config.conf file with all required configurations fields
        with resources.path(__package__, "config.conf") as pg_config_path:
            self.config: Dict[str, Any] = ConfigFactory.parse_file(pg_config_path)

    async def setup(self) -> None:
        self.web_server = WebServerBase()

    async def run(self) -> None:
        assert self.web_server is not None
        await self.web_server.start_web_server()

    async def aclose(self) -> None:
        if self.web_server:
            await self.web_server.aclose()


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
