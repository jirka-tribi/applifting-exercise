import logging
from functools import wraps
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, Callable

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from jose import JWTError, jwt
from schema import SchemaError

from .exceptions import (
    InvalidPassword,
    NewUserIsAlreadyExists,
    ProductIdNotExists,
    ProductIdNotInt,
    UserIsNotExists,
)

if TYPE_CHECKING:
    from .web import WebServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] - %(levelname)-8s %(name)s: %(message)s",
)
LOGGER = logging.getLogger(__name__)


@web.middleware
async def error_middleware(request: Request, handler: Callable[..., Any]) -> Response:
    # Middleware for handling and returning all exceptions as json response
    try:
        response: Response = await handler(request)

    except JSONDecodeError:
        err_msg = "JSON data required"
        LOGGER.exception(err_msg)
        return web.json_response({"error": err_msg}, status=400)

    except SchemaError as e:
        LOGGER.exception("Validation of data in request failed")
        return web.json_response({"error": str(e)}, status=400)

    except (NewUserIsAlreadyExists, InvalidPassword, UserIsNotExists):
        err_msg = "Invalid username or password"
        LOGGER.exception(err_msg)
        return web.json_response({"error": err_msg}, status=401)

    except ProductIdNotInt:
        err_msg = "Product ID should be int"
        LOGGER.exception(err_msg)
        return web.json_response({"error": err_msg}, status=400)

    except ProductIdNotExists:
        err_msg = "Product ID not found"
        LOGGER.exception(err_msg)
        return web.json_response({"error": err_msg}, status=404)

    except Exception:  # pylint: disable=broad-except
        err_msg = "Server got itself in trouble"
        LOGGER.exception(err_msg)
        return web.json_response({"error": err_msg}, status=500)

    return response


@web.middleware
def auth_token_validate() -> Callable[..., Any]:
    # Decorator use for route handlers which should be protected by jwt token
    # Used similarly as aiohttp middleware but only for desired routes (not for all)
    def wrapped(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(web_server_instance: "WebServer", request: Request) -> Any:
            if "Authorization" in request.headers:
                authorization_string = request.headers["Authorization"]
            else:
                return web.Response(
                    text="Authorization field in HTTP header is required",
                    status=401,
                )

            if authorization_string[:7] == "Bearer ":
                authorization_token = authorization_string[7:]
            else:
                return web.Response(
                    text="Invalid Authorization Bearer field in HTTP header",
                    status=401,
                )

            try:
                internal_token = request.app["app_internal_token"]
                result = jwt.decode(authorization_token, internal_token, algorithms="HS256")
                LOGGER.info("User %s is authorized" % result["username"])
            except JWTError as e:
                LOGGER.exception("JWT decode failed")
                return web.Response(text=str(e), status=401)

            return await func(web_server_instance, request)

        return wrapper

    return wrapped
