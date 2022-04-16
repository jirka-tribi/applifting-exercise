import logging
from importlib import resources
from importlib.metadata import version

from aiohttp import web
from aiohttp.web_fileresponse import FileResponse
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from .core import Core

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] - %(levelname)-8s %(name)s: %(message)s",
)
LOGGER = logging.getLogger(__name__)


class WebServer:
    def __init__(self, core: Core) -> None:
        self._core = core

        self._web_app_base = web.Application()
        self._add_routes()

        self._runner = web.AppRunner(self._web_app_base)

    def _add_routes(self) -> None:
        self._web_app_base.router.add_route("GET", "/", self.basic_info)
        self._web_app_base.router.add_route("GET", "/favicon.ico", self.favicon)
        self._web_app_base.router.add_route("GET", "/status", self.status)

    async def start_web_server(self) -> None:
        LOGGER.info("Start web server")
        await self._runner.setup()
        # Default host `0.0.0.0` and port `8080`
        site = web.TCPSite(self._runner)
        await site.start()

    @staticmethod
    async def basic_info(_: Request) -> Response:
        # Return simple html with basic info (app name and version)

        html = (
            f"<p style='font-size: 22px'>"
            f"App Name:&nbsp;&nbsp;&nbsp;&nbsp;<strong>{__package__}</strong></h2><br> "
            f"App Version:&nbsp;<strong>{version(__package__)}</strong></p><br>"
        )

        return Response(text=html, content_type="text/html")

    @staticmethod
    async def favicon(_: Request) -> FileResponse:
        with resources.path(__package__, "data") as data_dir_path:
            favicon_path = data_dir_path.joinpath("favicon.ico")

        return FileResponse(favicon_path)

    async def status(self, _: Request) -> Response:
        # Could be used in kubernetes as liveness probe
        # Return 200 when app is alive else 500

        status = 200 if await self._core.is_alive() else 500

        return Response(status=status)

    async def aclose(self) -> None:
        LOGGER.info("Closing web server")
        await self._runner.shutdown()
        await self._runner.cleanup()
