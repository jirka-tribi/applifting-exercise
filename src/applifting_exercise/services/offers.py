import asyncio
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, Union

from aiohttp import ClientError, ClientSession

from ..models import Offer, Product

LOGGER = logging.getLogger(__name__)


class OffersService:
    def __init__(self, offers_config: Dict[str, Union[str, int]]) -> None:
        self._offers_service_url = offers_config["offers_service_url"]
        self._semaphore = asyncio.Semaphore(int(offers_config["offers_service_concurrency"]))

        self._client_session = ClientSession()
        self._auth_header: Optional[Dict[str, str]] = None

    async def _get_auth_token(self) -> str:
        async with self._client_session.post(
            f"{self._offers_service_url}/auth",
        ) as response:
            resp = await response.json()

        return str(resp["access_token"])

    async def store_auth_header(self) -> None:
        auth_token = await self._get_auth_token()
        self._auth_header = {"Bearer": auth_token}

    async def register_product(self, product: Product) -> bool:
        # Try register product into offer service
        # Return True if register was successful

        assert self._auth_header is not None

        try:
            async with self._client_session.post(
                f"{self._offers_service_url}/products/register",
                headers=self._auth_header,
                raise_for_status=True,
                json=asdict(product),
            ) as _:
                pass
        except ClientError:
            LOGGER.error("Register product to offers service failed")
            return False

        return True

    async def get_offers(self, product_id: int) -> Optional[List[Offer]]:
        assert self._auth_header is not None
        get_offer_at = datetime.utcnow()

        async with self._semaphore:
            try:
                async with self._client_session.get(
                    f"{self._offers_service_url}/products/{product_id}/offers",
                    headers=self._auth_header,
                    raise_for_status=True,
                ) as response:
                    offers_response_list = await response.json()
            except ClientError:
                LOGGER.warning("Call to offers service failed")
                return None

        offers_list = [
            Offer(**offer, product_id=product_id, created_at=get_offer_at)
            for offer in offers_response_list
        ]

        return offers_list

    async def aclose(self) -> None:
        await self._client_session.close()
