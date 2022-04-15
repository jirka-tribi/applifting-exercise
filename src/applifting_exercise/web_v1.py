from aiohttp import web

PREFIX_V1 = "/api/v1"


class WebApiV1:
    def __init__(self):
        self.web_api_v1 = web.Application()

        self._add_routes()

    @property
    def return_v1(self):
        return self.web_api_v1

    def _add_routes(self):
        self.web_api_v1.router.add_route("GET", "/test", self.test_v1)

    @staticmethod
    async def test_v1(_: web.Request) -> web.Response:
        return web.Response(text="V1 JEDE")
