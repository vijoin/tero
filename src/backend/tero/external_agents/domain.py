from typing import Any, Optional
from datetime import datetime
import base64

from sqlmodel import Field, Relationship
from sqlmodel import Column
import sqlalchemy as sa

from ..core.domain import CamelCaseModel
from ..users.domain import User


class ExternalAgent(CamelCaseModel, table=True):
    __tablename__: Any = "external_agent"
    id: int = Field(primary_key=True, default=None)
    name: Optional[str] = Field(max_length=30, default=None, unique=True)   
    icon: Optional[bytes] = Field(default=None, sa_column=Column(sa.LargeBinary))


class ExternalAgentTimeSaving(CamelCaseModel, table=True):
    __tablename__: Any = "external_agent_time_saving"
    id: int = Field(primary_key=True, default=None)
    user_id: int = Field(foreign_key="user.id", index=True)
    external_agent_id: int = Field(foreign_key="external_agent.id", index=True)
    minutes_saved: int = Field(gt=0)
    date: datetime = Field(default_factory=datetime.now)
    user: User = Relationship()
    external_agent: ExternalAgent = Relationship()


class PublicExternalAgent(CamelCaseModel):
    id: int
    name: str
    icon: Optional[str] = None

    @staticmethod
    def from_agent(a: ExternalAgent) -> 'PublicExternalAgent':
        agent_dict = a.model_dump()
        agent_dict["icon"] = base64.b64encode(agent_dict["icon"]).decode("utf-8") if agent_dict.get("icon") else None
        return PublicExternalAgent.model_validate(agent_dict)



class NewExternalAgent(CamelCaseModel):
    name: str
    icon: Optional[bytes] = None


class NewExternalAgentTimeSaving(CamelCaseModel):
    date: datetime
    minutes_saved: int = Field(gt=0)