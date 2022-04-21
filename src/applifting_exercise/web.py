import logging
from dataclasses import asdict
from importlib import resources
from importlib.metadata import version

from aiohttp import web
from aiohttp.web_fileresponse import FileResponse
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_urldispatcher import UrlMappingMatchInfo

from .core import Core
from .exceptions import ProductIdNotInt
from .models import PRODUCT_SCHEMA, USER_REQUEST_SCHEMA, Product, PRICES_FROM_TO_SCHEMA
from .web_middlewares import auth_token_validate, error_middleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] - %(levelname)-8s %(name)s: %(message)s",
)
LOGGER = logging.getLogger(__name__)

PREFIX_V1 = "/api/v1"


def validate_product_id(match_info: UrlMappingMatchInfo) -> int:
    try:
        product_id = int(match_info["product_id"])
    except ValueError as e:
        raise ProductIdNotInt from e

    return product_id


class WebServer:
    def __init__(self, core: Core) -> None:
        self._core = core

        self._web_app_v1 = web.Application(middlewares=[error_middleware])
        self._web_app_v1["app_internal_token"] = self._core.app_internal_token

        self._web_app_base = web.Application()

        self._add_routes()
        self._web_app_base.add_subapp(PREFIX_V1, self._web_app_v1)
        self._runner = web.AppRunner(self._web_app_base)

    def _add_routes(self) -> None:
        self._web_app_v1.router.add_route("POST", "/register", self.register)
        self._web_app_v1.router.add_route("POST", "/login", self.login)

        self._web_app_v1.router.add_route("POST", "/products", self.create_product)
        self._web_app_v1.router.add_route("GET", "/products/{product_id}", self.get_product)
        self._web_app_v1.router.add_route("PUT", "/products/{product_id}", self.update_product)
        self._web_app_v1.router.add_route("DELETE", "/products/{product_id}", self.delete_product)

        self._web_app_v1.router.add_route("GET", "/products/{product_id}/offers", self.get_offers)
        self._web_app_v1.router.add_route(
            "GET", "/products/{product_id}/offers_all", self.get_offers_all
        )
        self._web_app_v1.router.add_route("GET", "/products/{product_id}/prices", self.get_prices)

        self._web_app_base.router.add_route("GET", "/", self.basic_info)
        self._web_app_base.router.add_route("GET", "/favicon.ico", self.favicon)
        self._web_app_base.router.add_route("GET", "/status", self.status)

    async def start_web_server(self) -> None:
        LOGGER.info("Start web server")
        await self._runner.setup()
        # Default host `0.0.0.0` and port `8080`
        site = web.TCPSite(self._runner)
        await site.start()

    async def register(self, request: Request) -> Response:
        data = await request.json()
        validated_user = USER_REQUEST_SCHEMA.validate(data)

        token = await self._core.register(
            validated_user["username"].strip(), validated_user["password"].strip()
        )

        return web.json_response({"token": token})

    async def login(self, request: Request) -> Response:
        data = await request.json()
        validated_user = USER_REQUEST_SCHEMA.validate(data)

        token = await self._core.login(
            validated_user["username"].strip(), validated_user["password"].strip()
        )

        return web.json_response({"token": token})

    @auth_token_validate()
    async def create_product(self, request: Request) -> Response:
        data = await request.json()
        validated_product = PRODUCT_SCHEMA.validate(data)

        product_id = await self._core.create_product(
            validated_product["name"], validated_product["description"]
        )

        return web.json_response({"id": product_id}, status=201)

    async def get_product(self, request: Request) -> Response:
        product_id = validate_product_id(request.match_info)

        product = await self._core.get_product(product_id)

        return web.json_response(asdict(product))

    @auth_token_validate()
    async def update_product(self, request: Request) -> Response:
        product_id = validate_product_id(request.match_info)

        data = await request.json()
        validated_product_update = PRODUCT_SCHEMA.validate(data)

        product_to_update = Product(
            product_id, validated_product_update["name"], validated_product_update["description"]
        )

        await self._core.update_product(product_to_update)

        return web.json_response({})

    @auth_token_validate()
    async def delete_product(self, request: Request) -> Response:
        product_id = validate_product_id(request.match_info)

        await self._core.delete_product(product_id)

        return web.json_response({})

    async def get_offers(self, request: Request) -> Response:
        product_id = validate_product_id(request.match_info)

        offers_list = await self._core.get_offers(product_id)

        return web.json_response({"offers": [offer.for_api for offer in offers_list]})

    async def get_offers_all(self, request: Request) -> Response:
        product_id = validate_product_id(request.match_info)

        offers_list = await self._core.get_offers_all(product_id)

        return web.json_response({"offers": [offer.for_api for offer in offers_list]})

    async def get_prices(self, request: Request) -> Response:
        product_id = validate_product_id(request.match_info)
        data = await request.json()

        validated_prices_date = PRICES_FROM_TO_SCHEMA.validate(data)
        from_date = validated_prices_date["from_date"]
        to_date = validated_prices_date["to_date"]

        prices_from_to, percentage = await self._core.get_prices(product_id, from_date, to_date)

        return web.json_response(
            {"prices": [price.value for price in prices_from_to], "percentage": percentage}
        )

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
