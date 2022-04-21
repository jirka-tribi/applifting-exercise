# pylint: disable=unused-argument

from datetime import datetime
from typing import Dict

import pytest
from aiohttp import ClientSession
from applifting_exercise.database import Database
from applifting_exercise.models import Offer

INVALID_JSON_DATA = [
    {"from_date": "invalid_time", "to_date": "invalid_time"},
    {"invalid_key": "2022-04-21T10:10:37", "to_date": "2022-04-21T16:10:37"},
    {"from_date": "2022-04-21T10:10:37", "invalid_key": "2022-04-21T16:10:37"},
    {},
]


@pytest.mark.parametrize("invalid_json_data", INVALID_JSON_DATA)
async def test_invalid_data(
    prepared_db: Database,
    test_web_server: None,
    api_url_v1: str,
    invalid_json_data: Dict[str, str],
) -> None:

    async with ClientSession() as session:
        async with session.get(
            f"{api_url_v1}/products/1/prices", json=invalid_json_data
        ) as response:
            assert response.status == 400


FROM_TO_PRICES_JSON = {"from_date": "2022-04-21T10:00:00", "to_date": "2022-04-21T16:00:00"}


async def test_prices_rise(prepared_db: Database, test_web_server: None, api_url_v1: str) -> None:

    product_id = (await prepared_db.create_product("Product Name", "Product Description")).id

    offer_1 = Offer(1, product_id, 100, 5, datetime.fromisoformat("2022-04-21T11:00:00"))
    offer_2 = Offer(2, product_id, 200, 5, datetime.fromisoformat("2022-04-21T12:00:00"))

    await prepared_db.insert_new_offers([offer_1, offer_2])

    async with ClientSession() as session:
        async with session.get(
            f"{api_url_v1}/products/{product_id}/prices", json=FROM_TO_PRICES_JSON
        ) as response:
            assert response.status == 200
            prices_json = await response.json()

    assert prices_json == {"percentage": 100, "prices": [100, 200]}


async def test_prices_fall(prepared_db: Database, test_web_server: None, api_url_v1: str) -> None:

    product_id = (await prepared_db.create_product("Product Name", "Product Description")).id

    offer_1 = Offer(1, product_id, 200, 5, datetime.fromisoformat("2022-04-21T11:00:00"))
    offer_2 = Offer(2, product_id, 100, 5, datetime.fromisoformat("2022-04-21T12:00:00"))

    await prepared_db.insert_new_offers([offer_1, offer_2])

    async with ClientSession() as session:
        async with session.get(
            f"{api_url_v1}/products/{product_id}/prices", json=FROM_TO_PRICES_JSON
        ) as response:
            assert response.status == 200
            prices_json = await response.json()

    assert prices_json == {"percentage": 50, "prices": [200, 100]}
