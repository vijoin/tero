from typing import List, Optional

from ..core.env import env
from .core import AgentTool
from .docs import DocsTool
from .jira import JiraTool
from .mcp import McpTool
from .web import WebTool
from .browser import BrowserTool

class ToolRepository:

    def __init__(self):
        self._tools: List[AgentTool] = [DocsTool(), McpTool(), JiraTool(), BrowserTool()]
        
        if env.web_tool_tavily_api_key or (env.web_tool_google_api_key and env.web_tool_google_custom_search_engine_id):
            self._tools.append(WebTool())

    def find_agent_tools(self) -> List[AgentTool]:
        return self._tools

    def find_by_id(self, tool_id: str) -> Optional[AgentTool]:
        return next((t for t in self._tools if t.id == tool_id or t.id.endswith("-*") and tool_id.startswith(t.id[:-1])), None)
