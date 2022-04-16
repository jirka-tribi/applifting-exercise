from datetime import datetime, timedelta

import bcrypt
from jose import jwt

from .database import Database
from .exceptions import InvalidPassword, UserIsExists, UserIsNotExists


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
        if await self._db.is_user_exists(username):
            raise UserIsExists

        hashed_pwd = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        # Store new user and hashed password into DB
        user_id = await self._db.register_user(username, hashed_pwd)

        return self._generate_token(user_id, username)

    async def login(self, username: str, password: str) -> str:
        user = await self._db.get_user(username)

        if user is None:
            raise UserIsNotExists

        if not bcrypt.checkpw(password.encode(), user.hashed_pwd):
            raise InvalidPassword

        return self._generate_token(user.id, user.username)

    async def is_alive(self) -> bool:
        return await self._db.is_connected()
