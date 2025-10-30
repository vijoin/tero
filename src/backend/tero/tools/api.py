import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from ..agents.repos import AgentToolConfigRepository
from ..core.api import BASE_PATH
from ..core.auth import get_current_user
from ..core.repos import get_db
from ..tools.oauth import ToolOAuthCallbackError, ToolAuthCallback, ToolOAuthRepository
from ..users.domain import User
from .core import AgentTool
from .repos import ToolRepository


logger = logging.getLogger(__name__)
router = APIRouter()
TOOLS_PATH = f"{BASE_PATH}/tools"


@router.get(TOOLS_PATH)
# user is added to contract just to require authentication to get the available agent tools
async def find_agent_tools(_: Annotated[User, Depends(get_current_user)]) -> List[AgentTool]:
    return ToolRepository().find_agent_tools()


@router.post(f"{TOOLS_PATH}/{{tool_id}}/oauth-callback")
async def tool_auth(tool_id: str, callback: ToolAuthCallback, user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    tool = ToolRepository().find_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    oauth_repo = ToolOAuthRepository(db)
    state = await oauth_repo.find_state(user.id, tool_id, callback.state)
    if not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    config = await AgentToolConfigRepository(db).find_by_ids(state.agent_id, tool_id, include_drafts=True)
    if not config:
        # this should not happen since for the state to exist a configuration must exist as well
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    await oauth_repo.delete_state(user.id, state.agent_id, tool_id)
    if not callback.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authentication cancelled")
    tool.configure(config.agent, user.id, config.config, db)
    try:
        await tool.auth(callback, state)
    except ToolOAuthCallbackError:
        logger.exception(f"Error during tool oauth callback for tool {tool_id} and user {user.id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
