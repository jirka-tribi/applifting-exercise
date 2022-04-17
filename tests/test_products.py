# pylint: disable=unused-argument

from typing import Dict

import pytest
from aiohttp import ClientSession
from applifting_exercise.database import Database

INVALID_JSON_DATA = [
    {"name": "", "description": "Product Description"},
    {"invalid_key": "Product Name", "description": "Product Description"},
    {"name": "Product Name", "invalid_key": "Product Description"},
    {},
]


@pytest.mark.parametrize("invalid_json_data", INVALID_JSON_DATA)
async def test_invalid_input_data(
    test_web_server: None,
    api_url_v1: str,
    jwt_testing_token: str,
    invalid_json_data: Dict[str, str],
) -> None:

    # All invalid input data should return 400
    async with ClientSession() as session:
        async with session.post(
            f"{api_url_v1}/products/create",
            json=invalid_json_data,
            headers={"Authorization": f"Bearer {jwt_testing_token}"},
        ) as response:
            assert response.status == 400

        async with session.put(
            f"{api_url_v1}/products/1/update",
            json=invalid_json_data,
            headers={"Authorization": f"Bearer {jwt_testing_token}"},
        ) as response:
            assert response.status == 400


async def test_invalid_path(
    test_web_server: None,
    api_url_v1: str,
    jwt_testing_token: str,
) -> None:

    # All invalid input data should return 400
    async with ClientSession() as session:
        async with session.put(
            f"{api_url_v1}/products/invalid_name/update",
            headers={"Authorization": f"Bearer {jwt_testing_token}"},
        ) as response:
            assert response.status == 400

        update_product_json = {
            "name": "Product Name Updated",
            "description": "Product Description Updated",
        }

        async with session.put(
            f"{api_url_v1}/products/100/update",
            json=update_product_json,
            headers={"Authorization": f"Bearer {jwt_testing_token}"},
        ) as response:
            assert response.status == 404

        async with session.delete(
            f"{api_url_v1}/products/invalid_name/delete",
            headers={"Authorization": f"Bearer {jwt_testing_token}"},
        ) as response:
            assert response.status == 400

        async with session.delete(
            f"{api_url_v1}/products/100/delete",
            json=update_product_json,
            headers={"Authorization": f"Bearer {jwt_testing_token}"},
        ) as response:
            assert response.status == 404


async def test_create_product(
    prepared_db: Database, test_web_server: None, api_url_v1: str, jwt_testing_token: str
) -> None:

    create_product_json = {
        "name": "Product Name",
        "description": "Product Description",
    }

    async with ClientSession() as session:
        async with session.post(
            f"{api_url_v1}/products/create",
            json=create_product_json,
            headers={"Authorization": f"Bearer {jwt_testing_token}"},
        ) as response:
            assert response.status == 201

    product = await prepared_db.get_product(1)
    assert product is not None
    assert product.name == "Product Name"
    assert product.description == "Product Description"


async def test_update_product(
    prepared_db: Database, test_web_server: None, api_url_v1: str, jwt_testing_token: str
) -> None:

    product_id = await prepared_db.create_product("Product Name", "Product Description")

    update_product_json = {
        "name": "Product Name Updated",
        "description": "Product Description Updated",
    }

    async with ClientSession() as session:
        async with session.put(
            f"{api_url_v1}/products/{product_id}/update",
            json=update_product_json,
            headers={"Authorization": f"Bearer {jwt_testing_token}"},
        ) as response:
            assert response.status == 200

    product = await prepared_db.get_product(product_id)
    assert product is not None
    assert product.name == "Product Name Updated"
    assert product.description == "Product Description Updated"


async def test_delete_product(
    prepared_db: Database, test_web_server: None, api_url_v1: str, jwt_testing_token: str
) -> None:

    product_id = await prepared_db.create_product("Product Name", "Product Description")

    async with ClientSession() as session:
        async with session.delete(
            f"{api_url_v1}/products/{product_id}/delete",
            headers={"Authorization": f"Bearer {jwt_testing_token}"},
        ) as response:
            assert response.status == 200

    product = await prepared_db.get_product(product_id)
    assert product is None
