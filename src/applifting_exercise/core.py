from datetime import datetime, timedelta

import bcrypt
from jose import jwt

from .database import Database
from .exceptions import (
    InvalidPassword,
    NewUserIsAlreadyExists,
    ProductIdNotExists,
    UserIsNotExists,
)
from .models import Product


class Core:
    def __init__(self, db: Database, app_internal_token: str) -> None:
        self._db = db

        self.app_internal_token = app_internal_token

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
        product_id = await self._db.create_product(name, description)

        return product_id

    async def update_product(self, product: Product) -> None:
        updated = await self._db.update_product(product)

        if updated != "UPDATE 1":
            raise ProductIdNotExists

    async def delete_product(self, product_id: int) -> None:
        deleted = await self._db.delete_product(product_id)

        if deleted != "DELETE 1":
            raise ProductIdNotExists

    async def is_alive(self) -> bool:
        return await self._db.is_connected()
