import logging
from importlib.metadata import version

from aiohttp import web
from aiohttp.web_request import Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] - %(levelname)-8s %(name)s: %(message)s",
)
LOGGER = logging.getLogger(__name__)


class WebServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port

        self.web_app = web.Application()
        self.runner = web.AppRunner(self.web_app)

    def _add_routes(self) -> None:
        self.web_app.router.add_route("GET", "/", self.get_all_routes)

    async def start_web_server(self) -> None:
        LOGGER.info("Start web server")
        self._add_routes()
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

    async def get_all_routes(self, _: Request) -> web.Response:
        routes_list = []

        for resource in self.web_app.router.resources():
            resource_path = [resource.get_info()["path"]]
            for route in resource:
                resource_path.append(route.method)

            routes_list.append(resource_path)

        routes_list.sort()
        html = (
            f"<p style='font-size: 22px'>"
            f"App Name:&nbsp;&nbsp;&nbsp;&nbsp;<strong>{__package__}</strong></h2><br> "
            f"App Version:&nbsp;<strong>{version(__package__)}</strong></p><br>"
            "<p style='font-size: 18px'>Available endpoints:</p><table>"
        )

        for route_item in routes_list:
            endpoint_method = route_item[1]
            endpoint_link = route_item[0]
            html += f"<tr><td>{endpoint_method}</td><td style='padding-left:1em'>" \
                    f"<a href='{endpoint_link}'>{endpoint_link}</a></td></tr>"

        html += "</table>"

        return web.Response(text=html, content_type="text/html")

    async def aclose(self) -> None:
        await self.runner.shutdown()
        await self.runner.cleanup()
