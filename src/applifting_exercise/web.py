import logging
from importlib.metadata import version

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_pydantic import PydanticView, oas
from jose import jwt
from jose.exceptions import JWTError
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] - %(levelname)-8s %(name)s: %(message)s",
)
LOGGER = logging.getLogger(__name__)

ROUTES_WITHOUT_AUTH = ["/test"]


@web.middleware
async def auth_validate(request, handler):
    if request.match_info.get_info()["path"] in ROUTES_WITHOUT_AUTH:
        return await handler(request)

    if "Authorization" in request.headers:
        authorization_string = request.headers["Authorization"]
    else:
        return web.Response(
            text="Authorization field in HTTP header is required",
            status=401,
        )
    if authorization_string[:7] == "Bearer ":
        authorization_token = authorization_string[:7]
    else:
        return web.Response(
            text="Invalid Authorization Bearer field in HTTP header",
            status=401,
        )
    try:
        result = jwt.decode(authorization_token, "TEST_PASSWORD", algorithms=["RS256"])
        LOGGER.info("User %s is authorized" % result)
    except JWTError as e:
        LOGGER.exception(e)
        return web.Response(text=str(e), status=401)

    return await handler(request)


class TestResponse(BaseModel):
    test_string_1: str
    test_string_2: str


class TestRequest(BaseModel):
    test_string: str = Field(..., min_length=10, max_length=15)


class PydanticViewWithDB(PydanticView):
    def __init__(self, request: Request) -> None:
        super().__init__(request)
        self.database: TestDB = self.request.app.database


class TestView(PydanticViewWithDB):
    async def get(self, request: TestRequest) -> Response:
        test_string_1 = request.test_string
        test_string_2 = await self.database.get_item()

        response = TestResponse(test_string_1=test_string_1, test_string_2=test_string_2)

        return web.json_response(response.dict())


class WebServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port

        self.web_app = web.Application(middlewares=[auth_validate])
        self.runner = web.AppRunner(self.web_app)
        oas.setup(self.web_app, url_prefix="/api")

        database = TestDB()
        setattr(self.web_app, "database", database)

    def _add_routes(self) -> None:
        self.web_app.router.add_route("GET", "/", self.get_all_routes)
        self.web_app.router.add_route("GET", "/test", TestView)

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
            html += (
                f"<tr><td>{endpoint_method}</td><td style='padding-left:1em'>"
                f"<a href='{endpoint_link}'>{endpoint_link}</a></td></tr>"
            )

        html += "</table>"

        return web.Response(text=html, content_type="text/html")

    async def aclose(self) -> None:
        await self.runner.shutdown()
        await self.runner.cleanup()


class TestDB:
    def __init__(self) -> None:
        self.test_string = "TEST_STRING"

    async def get_item(self) -> str:
        return self.test_string
