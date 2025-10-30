from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core.api import MCP_PATH
from ..core.auth import get_current_user
from ..core.repos import get_db
from ..external_agents.domain import ExternalAgentTimeSaving
from ..external_agents.repos import (
    ExternalAgentRepository,
    ExternalAgentTimeSavingRepository,
)
from ..users.domain import User

router = APIRouter()

@router.post(f"{MCP_PATH}/add-time-saving", operation_id="add-time-saving")
async def add_time_saving(
        minutes_saved: Annotated[int, Query(description="The estimated number of minutes saved while using the external agent")], 
        agent_name: Annotated[str, Query(description="The name of the external AI agent")], 
        user: Annotated[User, Depends(get_current_user)], 
        db: Annotated[AsyncSession, Depends(get_db)]
    ) -> ExternalAgentTimeSaving:
    """
    Record time savings from using external AI agents.
    
    This tool allows users to track and record the estimated time they saved
    while using external AI agents, similar to the 'Register other agents' button
    in the AI Console.
    """
    external_agent = await ExternalAgentRepository(db).find_by_name(agent_name)
    if not external_agent:
        raise HTTPException(status_code=404, detail=f"External agent {agent_name} not found")
    return await ExternalAgentTimeSavingRepository(db).add_time_saving(ExternalAgentTimeSaving(
        user_id=user.id, 
        minutes_saved=minutes_saved, 
        external_agent_id=external_agent.id
    ))