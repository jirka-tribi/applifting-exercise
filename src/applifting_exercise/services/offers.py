import asyncio
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, Union

from aiohttp import ClientError, ClientSession

from ..models import Offer, Product

LOGGER = logging.getLogger(__name__)


class OffersService:
    def __init__(
        self,
        client_session: ClientSession,
        auth_header: Dict[str, str],
        offers_config: Dict[str, Union[str, int]],
    ) -> None:

        self._client_session = client_session
        self._auth_header = auth_header

        self._offers_service_url = offers_config["offers_service_url"]
        self._semaphore = asyncio.Semaphore(
            int(offers_config["offers_service_concurrency"])
        )

    @classmethod
    async def async_init(
        cls, offers_config: Dict[str, Union[str, int]]
    ) -> "OffersService":

        client_session = ClientSession()
        offers_service_url = offers_config["offers_service_url"]

        async with client_session.post(
            f"{offers_service_url}/auth",
        ) as response:
            resp = await response.json()

        auth_token = str(resp["access_token"])

        return cls(client_session, {"Bearer": auth_token}, offers_config)

    async def register_product(self, product: Product) -> bool:
        # Try register product into offer service
        # Return True if register was successful

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
