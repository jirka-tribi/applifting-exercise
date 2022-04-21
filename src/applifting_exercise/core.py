import asyncio
from datetime import datetime, timedelta
from typing import List

import bcrypt
from jose import jwt

from .database import Database
from .exceptions import (
    InvalidPassword,
    NewUserIsAlreadyExists,
    ProductIdNotExists,
    UserIsNotExists,
)
from .models import Offer, Product
from .services import OffersService


class Core:
    def __init__(
        self, offers_service: OffersService, db: Database, app_internal_token: str
    ) -> None:

        self._offers_service = offers_service
        self._db = db

        self.app_internal_token = app_internal_token

    async def background_tasks(self) -> None:
        while True:
            await self._update_offers()
            await asyncio.sleep(60)

    def _generate_token(self, user_id: int, username: str) -> str:
        # Generate jwt token with expiration one hour
        generated_token = jwt.encode(
            {"id": user_id, "username": username, "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app_internal_token,
            algorithm="HS256",
        )

        return str(generated_token)

    async def register(self, username: str, password: str) -> str:
        hashed_pwd = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        # Check if user is exists and store new user and hashed password into DB
        user_id = await self._db.register_user(username, hashed_pwd)
        if not user_id:
            raise NewUserIsAlreadyExists

        return self._generate_token(user_id, username)

    async def login(self, username: str, password: str) -> str:
        user = await self._db.get_user(username)

        if user is None:
            raise UserIsNotExists

        if not bcrypt.checkpw(password.encode(), user.hashed_pwd):
            raise InvalidPassword

        return self._generate_token(user.id, user.username)

    async def create_product(self, name: str, description: str) -> int:
        product = await self._db.create_product(name, description)
        registered = await self._offers_service.register_product(product)

        # If register was not successful delete product from DB and raise RuntimeError
        if not registered:
            await self._db.delete_product(product.id)
            raise RuntimeError("Product was not registered into offers service")

        return product.id

    async def get_product(self, product_id: int) -> Product:
        product = await self._db.get_product(product_id)

        if not product:
            raise ProductIdNotExists

        return product

    async def update_product(self, product: Product) -> None:
        updated = await self._db.update_product(product)

        if updated != "UPDATE 1":
            raise ProductIdNotExists

    async def delete_product(self, product_id: int) -> None:
        deleted = await self._db.delete_product(product_id)

        if deleted != "DELETE 1":
            raise ProductIdNotExists

    async def get_offers(self, product_id: int) -> List[Offer]:
        offers_list = await self._db.get_offers(product_id)

        return offers_list

    async def get_offers_all(self, product_id: int) -> List[Offer]:
        offers_all_list = await self._db.get_offers_all(product_id)

        return offers_all_list

    async def _update_offers(self) -> None:
        products_ids = await self._db.get_all_products_ids()
        coroutines = [self._offers_service.get_offers(product_id) for product_id in products_ids]
        offers_results = await asyncio.gather(*coroutines)

        offers_list = []
        for offers in [offers for offers in offers_results if offers]:
            offers_list.extend(offers)

        await self._db.insert_new_offers(offers_list)

    async def is_alive(self) -> bool:
        return await self._db.is_connected()
