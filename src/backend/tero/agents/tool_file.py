import logging

from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.background import BackgroundTasks

from ..files.domain import File, FileStatus, FileMetadata
from ..files.file_quota import QuotaExceededError
from ..files.parser import add_encoding_to_content_type
from ..files.repos import FileRepository
from ..tools.core import AgentTool
from ..users.domain import User
from .domain import AgentToolConfigFile
from .repos import AgentToolConfigFileRepository


logger = logging.getLogger(__name__)


async def upload_tool_file(file: File, tool: AgentTool, agent_id: int, user: User, db: AsyncSession, background_tasks: BackgroundTasks) -> FileMetadata:
    file.content_type = add_encoding_to_content_type(file.content_type, file.content)
    file = await FileRepository(db).add(file)
    await AgentToolConfigFileRepository(db).add(AgentToolConfigFile(agent_id=agent_id, tool_id=tool.id, file_id=file.id))
    background_tasks.add_task(_add_tool_file, file, user, tool, db)
    return FileMetadata.from_file(file)


async def _add_tool_file(f: File, user: User, tool: AgentTool, db: AsyncSession):
    try:
        await tool.add_file(f, user)
        f.status = FileStatus.PROCESSED
    except QuotaExceededError:
        f.status = FileStatus.QUOTA_EXCEEDED
        logger.error(f"Quota exceeded for user {user.id} when adding tool file {f.id} {f.name}")
    except Exception as e:
        f.status = FileStatus.ERROR
        logger.error(f"Error adding tool file {f.id} {f.name} {e}", exc_info=True)
    finally:
        await FileRepository(db).update(f)
