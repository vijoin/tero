from fastapi import APIRouter, Depends, FastAPI
from fastapi.responses import RedirectResponse, Response
from fastapi_mcp import AuthConfig, FastApiMCP
import httpx

from .core.auth import get_current_user
from .core.env import env
from .external_agents.mcp_tools import router as external_agents_mcp_tools_router

FRONTEND_OPENID_URL = env.frontend_openid_url or env.openid_url

mcp_server_router = APIRouter()


@mcp_server_router.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource_forward():
    return RedirectResponse(url=f"{FRONTEND_OPENID_URL}/.well-known/oauth-protected-resource")


@mcp_server_router.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server_forward():
    return RedirectResponse(url=f"{FRONTEND_OPENID_URL}/.well-known/oauth-authorization-server")


# This is a workaround to allow the required-action page to load the css and js files
@mcp_server_router.get("/resources/{path:path}")
async def resources_forward(path: str):
    target_url = f"{env.openid_url.replace("/realms/tero", "")}/resources/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.get(target_url)
        return Response(content=response.content, status_code=response.status_code)


def setup_mcp_server(app: FastAPI):
    if not env.openid_url:
        return
    
    with httpx.Client() as client:
        response = client.get(f"{env.openid_url}/.well-known/openid-configuration")
        custom_oauth_metadata = response.json()
    
    mcp = FastApiMCP(
        app,
        auth_config=AuthConfig(
            custom_oauth_metadata=custom_oauth_metadata,
            dependencies=[Depends(get_current_user)],
        )
    )
    mcp.mount_http()
    app.include_router(external_agents_mcp_tools_router)
    mcp.setup_server()
    # include the mcp server router after the mcp server is setup to avoid capturing well-known or other non-tool endpoints as tools
    app.include_router(mcp_server_router)

