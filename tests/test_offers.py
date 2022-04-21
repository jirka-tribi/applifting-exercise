# pylint: disable=unused-argument, protected-access

from datetime import datetime, timedelta

from aiohttp import ClientSession
from aioresponses import aioresponses
from applifting_exercise.core import Core
from applifting_exercise.database import Database
from applifting_exercise.models import Offer
from applifting_exercise.services import OffersService
from freezegun.api import FrozenDateTimeFactory


async def test_get_offers(prepared_db: Database, test_web_server: None, api_url_v1: str) -> None:

    product_id = (await prepared_db.create_product("Product Name", "Product Description")).id

    offer_1 = Offer(1, product_id, 100, 5, datetime.utcnow())
    offer_2 = Offer(2, product_id, 200, 10, datetime.utcnow() + timedelta(hours=1))

    await prepared_db.insert_new_offers([offer_1, offer_2])

    async with ClientSession() as session:
        async with session.get(
            f"{api_url_v1}/products/{product_id}/offers",
        ) as response:
            assert response.status == 200
            offers_json = await response.json()

    assert offers_json == {"offers": [{"id": 1, "items_in_stock": 10, "price": 200}]}


async def test_get_offers_all(
    prepared_db: Database, test_web_server: None, api_url_v1: str
) -> None:

    product_id = (await prepared_db.create_product("Product Name", "Product Description")).id

    offer_1 = Offer(1, product_id, 100, 5, datetime.utcnow())
    offer_2 = Offer(2, product_id, 200, 10, datetime.utcnow())

    await prepared_db.insert_new_offers([offer_1, offer_2])

    async with ClientSession() as session:
        async with session.get(
            f"{api_url_v1}/products/{product_id}/offers_all",
        ) as response:
            assert response.status == 200
            offers_json = await response.json()

    assert offers_json == {
        "offers": [
            {"id": 1, "items_in_stock": 5, "price": 100},
            {"id": 1, "items_in_stock": 10, "price": 200},
        ]
    }


async def test_update_offers(
    offers_service: OffersService, prepared_db: Database, freezer: FrozenDateTimeFactory
) -> None:
    core = Core(offers_service=offers_service, db=prepared_db, app_internal_token="")

    product_id = (await prepared_db.create_product("Product Name", "Product Description")).id

    with aioresponses(passthrough=["http://localhost:"]) as mocked_aio_response:  # type: ignore
        mocked_aio_response.get(
            f"https://test-offers.com/api/v1/products/{product_id}/offers",
            payload=[{"id": 100, "price": 1000, "items_in_stock": 5}],
        )

        await core._update_offers()

    all_offers = await prepared_db.get_offers_all(product_id)

    assert all_offers == [
        Offer(id=100, product_id=1, price=1000, items_in_stock=5, created_at=datetime.utcnow())
    ]
