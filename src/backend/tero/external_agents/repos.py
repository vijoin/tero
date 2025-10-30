from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .domain import ExternalAgent, ExternalAgentTimeSaving


class ExternalAgentRepository:

    def __init__(self, db: AsyncSession):
        self._db = db
    
    async def find_by_id(self, external_agent_id: int) -> Optional[ExternalAgent]:
        stmt = (
            select(ExternalAgent).where(ExternalAgent.id == external_agent_id)
        )
        ret = await self._db.exec(stmt)
        return ret.one_or_none()

    async def find_by_name(self, name: str) -> Optional[ExternalAgent]:
        stmt = (
            select(ExternalAgent).where(ExternalAgent.name == name)
        )
        ret = await self._db.exec(stmt)
        return ret.one_or_none()

    async def find_all(self) -> List[ExternalAgent]:
        stmt = (
            select(ExternalAgent)
        )
        ret = await self._db.exec(stmt)
        return list(ret.all())
    
    async def add(self, external_agent: ExternalAgent) -> ExternalAgent:
        self._db.add(external_agent)
        await self._db.commit()
        await self._db.refresh(external_agent)
        return external_agent
    

class ExternalAgentTimeSavingRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def add_time_saving(self, time_saving: ExternalAgentTimeSaving) -> ExternalAgentTimeSaving:
        self._db.add(time_saving)
        await self._db.commit()
        await self._db.refresh(time_saving)
        return time_saving