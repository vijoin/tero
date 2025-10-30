import logging
from datetime import datetime, timezone
from typing import Annotated, List, cast

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from ...core.auth import get_current_user
from ...core.repos import get_db
from ...users.domain import User
from ...threads.repos import ThreadMessageRepository, ThreadRepository
from ...threads.domain import Thread, ThreadMessage, ThreadMessagePublic
from ..api import find_editable_agent, AGENT_PATH
from .domain import TestCase, PublicTestCase, NewTestCaseMessage, UpdateTestCaseMessage, UpdateTestCase, TestSuiteRun, TestSuiteRunStatus, RunTestSuiteRequest, TestCaseResult
from .repos import TestCaseRepository, TestCaseResultRepository, TestSuiteRunRepository
from .runner import cleanup_orphaned_suite_run, TestCaseRunner


TEST_CASES_PATH = f"{AGENT_PATH}/tests"


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(TEST_CASES_PATH, response_model=List[PublicTestCase])
async def find_test_cases(agent_id: int, user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)]) \
        -> List[TestCase]:
    agent = await find_editable_agent(agent_id, user, db)
    return await TestCaseRepository(db).find_by_agent(agent.id)


@router.post(TEST_CASES_PATH, response_model=PublicTestCase)
async def add_test_case(agent_id: int, user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)]) -> TestCase:
    agent = await find_editable_agent(agent_id, user, db)
    test_cases_repo = TestCaseRepository(db)
    test_cases = await test_cases_repo.find_by_agent(agent.id)
    thread = await ThreadRepository(db).add(
        Thread(
            agent_id=agent.id,
            user_id=user.id,
            is_test_case=True,
            name=f"Test Case #{len(test_cases) + 1}"
        )
    )
    return await test_cases_repo.save(
        TestCase(
            thread_id=thread.id,
            agent_id=agent.id,
        )
    )


TEST_SUITE_RUNS_PATH = f"{TEST_CASES_PATH}/runs"


@router.get(TEST_SUITE_RUNS_PATH)
async def get_test_suite_runs(agent_id: int, user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)], limit: int = 20, offset: int = 0) -> List[TestSuiteRun]:
    agent = await find_editable_agent(agent_id, user, db)
    return await TestSuiteRunRepository(db).find_by_agent_id(agent.id, limit=limit, offset=offset)


@router.post(TEST_SUITE_RUNS_PATH, status_code=status.HTTP_201_CREATED)
async def run_test_suite(
    agent_id: int, 
    request: RunTestSuiteRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks
) -> StreamingResponse:
    agent = await find_editable_agent(agent_id, user, db)
    all_test_cases = await TestCaseRepository(db).find_by_agent(agent.id)
    if not all_test_cases:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    
    if request.test_case_ids is not None:
        test_case_ids_set = set(request.test_case_ids)
        test_cases_to_run = [tc for tc in all_test_cases if tc.thread_id in test_case_ids_set]
        if not test_cases_to_run:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    else:
        test_cases_to_run = all_test_cases
    
    suite_repo = TestSuiteRunRepository(db)
    last_suite = await suite_repo.find_latest_by_agent_id(agent.id)
    if last_suite and last_suite.status == TestSuiteRunStatus.RUNNING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT)
    
    suite_run = await suite_repo.add(TestSuiteRun(
        agent_id=agent.id,
        status=TestSuiteRunStatus.RUNNING,
        total_tests=len(all_test_cases),
        passed_tests=0,
        failed_tests=0,
        error_tests=0,
        skipped_tests=0
    ))
    
    background_tasks.add_task(cleanup_orphaned_suite_run, suite_run.id, agent.id)
    
    return StreamingResponse(
        TestCaseRunner(db).run_test_suite_stream(agent, all_test_cases, test_cases_to_run, user.id, suite_run),
        media_type="text/event-stream",
    )


TEST_SUITE_RUN_PATH = f"{TEST_SUITE_RUNS_PATH}/{{suite_run_id}}"


@router.get(TEST_SUITE_RUN_PATH)
async def get_test_suite_run(agent_id: int, suite_run_id: int, user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)]) -> TestSuiteRun:
    return await _find_test_suite_run(suite_run_id, agent_id, user, db)


async def _find_test_suite_run(suite_run_id: int, agent_id: int, user: User, db: AsyncSession) -> TestSuiteRun:
    await find_editable_agent(agent_id, user, db)
    suite_run = await TestSuiteRunRepository(db).find_by_id_and_agent_id(suite_run_id, agent_id)
    if suite_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return suite_run


TEST_SUITE_RUN_RESULTS_PATH = f"{TEST_SUITE_RUN_PATH}/results"


@router.get(TEST_SUITE_RUN_RESULTS_PATH)
async def get_test_suite_run_results(agent_id: int, suite_run_id: int, user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)]) -> List[TestCaseResult]:
    await _find_test_suite_run(suite_run_id, agent_id, user, db)
    return await TestCaseResultRepository(db).find_by_suite_run_id(suite_run_id)


TEST_SUITE_RUN_RESULT_MESSAGE_PATH = f"{TEST_SUITE_RUN_RESULTS_PATH}/{{result_id}}/messages"


@router.get(TEST_SUITE_RUN_RESULT_MESSAGE_PATH, response_model=List[ThreadMessagePublic])
async def get_test_suite_run_result_messages(
    agent_id: int, 
    suite_run_id: int, 
    result_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[ThreadMessage]:
    await _find_test_suite_run(suite_run_id, agent_id, user, db)
    
    results_repo = TestCaseResultRepository(db)
    result = await results_repo.find_by_id_and_suite_run_id(result_id, suite_run_id)
    
    if result is None or result.thread_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return await ThreadMessageRepository(db).find_by_thread_id(result.thread_id)


TEST_CASE_PATH = f"{TEST_CASES_PATH}/{{test_case_id}}"


@router.get(TEST_CASE_PATH, response_model=PublicTestCase)
async def find_test_case(agent_id: int, test_case_id: int, user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)]) -> TestCase:
    return await _find_test_case(test_case_id, agent_id, user, db)


async def _find_test_case(test_case_id: int, agent_id: int, user: User, db: Annotated[AsyncSession, Depends(get_db)]) -> TestCase:
    await find_editable_agent(agent_id, user, db)
    test_case = await TestCaseRepository(db).find_by_id(test_case_id, agent_id)
    if test_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return test_case


@router.put(TEST_CASE_PATH, response_model=PublicTestCase)
async def update_test_case(agent_id: int, test_case_id: int, update: UpdateTestCase,
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)]) -> TestCase:
    test_case = await _find_test_case(test_case_id, agent_id, user, db)
    test_case.thread.name = update.name
    await ThreadRepository(db).update(test_case.thread)
    return test_case


@router.delete(TEST_CASE_PATH, status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(agent_id: int, test_case_id: int, user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)]) -> None:
    test_case = await _find_test_case(test_case_id, agent_id, user, db)
    await TestCaseRepository(db).delete(test_case)


TEST_CASE_MESSAGES_PATH = f"{TEST_CASE_PATH}/messages"


@router.get(TEST_CASE_MESSAGES_PATH, response_model=List[ThreadMessagePublic])
async def find_messages(agent_id: int, test_case_id: int, user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)]) -> List[ThreadMessage]:
    test_case = await _find_test_case(test_case_id, agent_id, user, db)
    return await ThreadMessageRepository(db).find_by_thread_id(test_case.thread_id)


@router.post(TEST_CASE_MESSAGES_PATH, response_model=ThreadMessagePublic)
async def add_message(agent_id: int, test_case_id: int, message: NewTestCaseMessage, user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)]) -> ThreadMessage:
    test_case = await _find_test_case(test_case_id, agent_id, user, db)
    repo = ThreadMessageRepository(db)
    added_message = await repo.add(ThreadMessage(
        thread_id=test_case.thread_id,
        text=message.text,
        origin=message.origin,
    ))
    test_case.last_update = added_message.timestamp
    await TestCaseRepository(db).save(test_case)
    return added_message


TEST_CASE_MESSAGE_PATH = f"{TEST_CASE_MESSAGES_PATH}/{{message_id}}"


@router.put(TEST_CASE_MESSAGE_PATH, response_model=ThreadMessagePublic)
async def update_message(agent_id: int, test_case_id: int, message_id: int, message: UpdateTestCaseMessage, user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)]) -> ThreadMessage:
    test_case = await _find_test_case(test_case_id, agent_id, user, db)
    repo = ThreadMessageRepository(db)
    test_case_message = await repo.find_by_id(message_id)
    if test_case_message is None or test_case_message.thread_id != test_case.thread_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    test_case_message.text = message.text
    await repo.update(test_case_message)
    test_case.last_update = datetime.now(timezone.utc)
    await TestCaseRepository(db).save(test_case)
    return test_case_message
