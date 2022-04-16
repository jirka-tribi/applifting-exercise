from .database import Database


class Core:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def is_alive(self) -> bool:
        return await self._db.is_connected()
