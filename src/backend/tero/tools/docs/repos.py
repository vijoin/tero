from typing import List, Optional

from sqlmodel import select, delete, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from ...core.repos import scalar
from .domain import DocToolFile, DocToolConfig


class DocToolFileRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def add(self, doc_tool_file: DocToolFile):
        await self._db.merge(doc_tool_file)
        await self._db.commit()

    async def find_by_agent_id(self, agent_id: int) -> List[DocToolFile]:
        ret = await self._db.exec(
            select(DocToolFile)
            .where(DocToolFile.agent_id == agent_id))
        return list(ret.all())

    async def find_by_agent_id_and_file_id(self, agent_id: int, file_id: int) -> Optional[DocToolFile]:
        stmt = (
            select(DocToolFile)
            .where(and_(DocToolFile.agent_id == agent_id, DocToolFile.file_id == file_id))
        )
        ret = await self._db.exec(stmt)
        return ret.one_or_none()

    async def remove(self, agent_id: int, file_id: int):
        stmt = (delete(DocToolFile)
                .where(and_(DocToolFile.agent_id == agent_id, DocToolFile.file_id == file_id)))
        await self._db.exec(scalar(stmt))
        await self._db.commit()

    async def remove_by_agent_id(self, agent_id: int):
        stmt = (delete(DocToolFile)
                .where(and_(DocToolFile.agent_id == agent_id)))
        await self._db.exec(scalar(stmt))
        await self._db.commit()


class DocToolConfigRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def add(self, doc_tool_config: DocToolConfig):
        await self._db.merge(doc_tool_config)
        await self._db.commit()

    async def remove(self, agent_id: int):
        stmt = (delete(DocToolConfig)
                .where(and_(DocToolConfig.agent_id == agent_id)))
        await self._db.exec(scalar(stmt))
        await self._db.commit()

    async def find_by_agent_id(self, agent_id) -> Optional[DocToolConfig]:
        ret = await self._db.exec(
            select(DocToolConfig)
            .where(DocToolConfig.agent_id == agent_id))
        return ret.one_or_none()
