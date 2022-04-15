import logging
from importlib import resources
from importlib.metadata import version

from aiohttp import web
from aiohttp.web_fileresponse import FileResponse
from aiohttp.web_request import Request
from aiohttp.web_response import Response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] - %(levelname)-8s %(name)s: %(message)s",
)
LOGGER = logging.getLogger(__name__)


class WebServerBase:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port

        self.web_app_base = web.Application()
        self._add_routes()
        self.runner = web.AppRunner(self.web_app_base)

        self.web_app_base.add_subapp(prefix=PREFIX_V1, subapp=WebAppV1().return_v1)

    def _add_routes(self) -> None:
        self.web_app_base.router.add_route("GET", "/", self.basic_info)
        self.web_app_base.router.add_route("GET", "/favicon.ico", self.favicon)
        self.web_app_base.router.add_route("GET", "/status", self.status)

    async def start_web_server(self) -> None:
        LOGGER.info("Start web server")
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
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

    @staticmethod
    async def status(_: Request) -> Response:
        # Could be used in kubernetes as liveness probe
        # Return 200 when app is alive else 500

        status = 200

        return Response(status=status)

    async def aclose(self) -> None:
        LOGGER.info("Closing web server")
        await self.runner.shutdown()
        await self.runner.cleanup()
