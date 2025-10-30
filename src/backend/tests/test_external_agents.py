from datetime import timedelta

from httpx import AsyncClient, Response

from .common import *

from tero.external_agents.api import EXTERNAL_AGENTS_PATH, EXTERNAL_AGENTS_TIME_SAVINGS_PATH
from tero.external_agents.domain import ExternalAgent
from tero.usage.api import IMPACT_PATH
from tero.usage.domain import ImpactSummary
from tero.teams.domain import MY_TEAM_ID


EXTERNAL_AGENT_ID = 1


@pytest.fixture(name="external_agents")
def external_agents_fixture() -> List[ExternalAgent]:
    return [ExternalAgent(id=1, name="ChatGPT"), 
            ExternalAgent(id=2, name="Cursor"), 
            ExternalAgent(id=3, name="Claude")]


async def test_find_external_agents(client: AsyncClient, external_agents: List[ExternalAgent]):
    resp = await _find_external_agents(client)
    assert_response(resp, [external_agents[0], external_agents[1], external_agents[2]])


async def _find_external_agents(client: AsyncClient) -> Response:
    return await client.get(EXTERNAL_AGENTS_PATH)


async def test_add_external_agent(client: AsyncClient, external_agents: List[ExternalAgent]):
    resp = await client.post(EXTERNAL_AGENTS_PATH, json={"name": "External Agent Test"})
    resp.raise_for_status()
    agents_resp = await _find_external_agents(client)
    assert_response(agents_resp, [external_agents[0], external_agents[1], external_agents[2], ExternalAgent(id=4, name="External Agent Test")])


async def test_add_external_agent_already_existing_name(client: AsyncClient, external_agents: List[ExternalAgent]):
    resp = await client.post(EXTERNAL_AGENTS_PATH, json={"name": "ChatGPT"})
    assert resp.status_code == 409
    agents_resp = await _find_external_agents(client)
    assert_response(agents_resp, [external_agents[0], external_agents[1], external_agents[2]])


@freeze_time(CURRENT_TIME)
async def test_add_external_agent_time_saving(client: AsyncClient):
    minutes_saved = 60
    resp = await _add_external_agent_time_saving(client, EXTERNAL_AGENT_ID, CURRENT_TIME - timedelta(days=1), minutes_saved)
    resp.raise_for_status()

    to_date = datetime.now()
    from_date = (to_date - timedelta(days=30))
    resp = await client.get(
        f"{IMPACT_PATH}/summary",
        params={"from_date": from_date.isoformat(), "to_date": to_date.isoformat(), "team_id": MY_TEAM_ID},
    )
    assert_response(resp, ImpactSummary(human_hours=160, ai_hours=5, previous_human_hours=160, previous_ai_hours=1))


async def _add_external_agent_time_saving(client: AsyncClient, external_agent_id: int, date: datetime, minutes_saved: int):
    return await client.post(EXTERNAL_AGENTS_TIME_SAVINGS_PATH.format(external_agent_id=external_agent_id), 
                             json={"date": date.isoformat(), "minutes_saved": minutes_saved})


async def test_add_external_agent_time_saving_zero_minutes(client: AsyncClient):
    resp = await _add_external_agent_time_saving(client, EXTERNAL_AGENT_ID, CURRENT_TIME, 0)
    assert resp.status_code == 422


async def test_add_external_agent_time_saving_negative_minutes(client: AsyncClient):
    resp = await _add_external_agent_time_saving(client, EXTERNAL_AGENT_ID, CURRENT_TIME, -5)
    assert resp.status_code == 422
