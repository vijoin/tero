from typing import List, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import select, delete, and_, col, func
from sqlmodel.ext.asyncio.session import AsyncSession

from ...core.repos import attr, scalar
from ...threads.domain import Thread
from ...threads.repos import ThreadRepository
from .domain import TestCase, TestCaseResult, TestSuiteRun


class TestCaseRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def find_by_id(self, test_case_id: int, agent_id: int) -> Optional[TestCase]:
        stmt = (
            select(TestCase)
            .join(Thread)
            .where(TestCase.thread_id == test_case_id, TestCase.agent_id == agent_id)
            .options(selectinload(attr(TestCase.thread))))
        ret = await self._db.exec(stmt)
        return ret.one_or_none()

    async def find_by_agent(self, agent_id: int) -> List[TestCase]:
        stmt = (
            select(TestCase)
            .join(Thread)
            .where(TestCase.agent_id == agent_id)
            .options(selectinload(attr(TestCase.thread)))
            .order_by(col(TestCase.thread_id)))
        ret = await self._db.exec(stmt)
        return list(ret.all())

    async def save(self, test_case: TestCase) -> TestCase:
        test_case = await self._db.merge(test_case)
        await self._db.commit()
        await self._db.refresh(test_case, ["thread"])
        return test_case

    async def delete(self, test_case: TestCase) -> None:
        result_stmt = select(TestCaseResult).where(and_(TestCaseResult.test_case_id == test_case.thread_id))
        result = await self._db.exec(result_stmt)
        test_case_results = list(result.all())
        
        delete_results_stmt = scalar(delete(TestCaseResult).where(and_(TestCaseResult.test_case_id == test_case.thread_id)))
        await self._db.exec(delete_results_stmt)
        
        delete_test_case_stmt = scalar(delete(TestCase).where(and_(TestCase.thread_id == test_case.thread_id)))
        await self._db.exec(delete_test_case_stmt)
        
        thread_repo = ThreadRepository(self._db)
        
        await thread_repo.delete(test_case.thread)
        
        for test_case_result in test_case_results:
            execution_thread_stmt = select(Thread).where(Thread.id == test_case_result.thread_id)
            execution_thread_result = await self._db.exec(execution_thread_stmt)
            execution_thread = execution_thread_result.one_or_none()
            if execution_thread:
                await thread_repo.delete(execution_thread)


class TestCaseResultRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def find_by_id_and_suite_run_id(self, result_id: int, suite_run_id: int) -> Optional[TestCaseResult]:
        stmt = (
            select(TestCaseResult)
            .where(TestCaseResult.id == result_id, TestCaseResult.test_suite_run_id == suite_run_id)
        )
        ret = await self._db.exec(stmt)
        return ret.one_or_none()

    async def save(self, result: TestCaseResult) -> TestCaseResult:
        result = await self._db.merge(result)
        await self._db.commit()
        await self._db.refresh(result)
        return result

    async def find_by_suite_run_id(self, suite_run_id: int) -> List[TestCaseResult]:
        stmt = (
            select(TestCaseResult)
            .where(TestCaseResult.test_suite_run_id == suite_run_id)
            .order_by(col(TestCaseResult.executed_at).desc(), col(TestCaseResult.id).desc())
        )
        ret = await self._db.exec(stmt)
        return list(ret.all())


class TestSuiteRunRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def find_by_id_and_agent_id(self, suite_run_id: int, agent_id: int) -> Optional[TestSuiteRun]:
        stmt = select(TestSuiteRun).where(TestSuiteRun.id == suite_run_id, TestSuiteRun.agent_id == agent_id)
        ret = await self._db.exec(stmt)
        return ret.one_or_none()

    async def find_by_agent_id(self, agent_id: int, limit: int = 20, offset: int = 0) -> List[TestSuiteRun]:
        stmt = (
            select(TestSuiteRun)
            .where(TestSuiteRun.agent_id == agent_id)
            .order_by(col(TestSuiteRun.executed_at).desc())
            .limit(limit)
            .offset(offset)
        )
        ret = await self._db.exec(stmt)
        return list(ret.all())

    async def find_latest_by_agent_id(self, agent_id: int) -> Optional[TestSuiteRun]:
        stmt = (
            select(TestSuiteRun)
            .where(TestSuiteRun.agent_id == agent_id)
            .order_by(col(TestSuiteRun.executed_at).desc())
            .limit(1)
        )
        ret = await self._db.exec(stmt)
        return ret.one_or_none()

    async def add(self, suite_run: TestSuiteRun) -> TestSuiteRun:
        self._db.add(suite_run)
        await self._db.commit()
        await self._db.refresh(suite_run)
        return suite_run

    async def save(self, suite_run: TestSuiteRun) -> TestSuiteRun:
        suite_run = await self._db.merge(suite_run)
        await self._db.commit()
        return suite_run
