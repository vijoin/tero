from datetime import datetime, timezone
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from .domain import File


class FileRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def add(self, file: File) -> File:
        self._db.add(file)
        await self._db.commit()
        await self._db.refresh(file, ['id'])
        return file

    async def find_by_id(self, file_id: int) -> Optional[File]:
        return await self._db.get(File, file_id)

    async def update(self, file: File):
        file.timestamp = datetime.now(timezone.utc)
        await self._db.merge(file)
        await self._db.commit()

    async def delete(self, file: File):
        await self._db.delete(file)
        await self._db.commit()
