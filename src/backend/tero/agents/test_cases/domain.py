from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, List

from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, Index

from ...core.domain import CamelCaseModel
from ...threads.domain import Thread
from ...threads.domain import ThreadMessageOrigin


class TestCase(SQLModel, table=True):
    __tablename__ : Any = "test_case"
    __table_args__ = (
        Index('ix_test_case_agent_id_last_update', 'agent_id', 'last_update'),
    )
    thread_id: int = Field(foreign_key="thread.id", primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    last_update: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thread: Thread = Relationship()


class TestCaseResultStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class TestSuiteRunStatus(Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

class TestCaseEventType(Enum):
    PHASE = "phase"
    USER_MESSAGE = "userMessage"
    AGENT_MESSAGE_START = "agentMessage.start"
    AGENT_MESSAGE_CHUNK = "agentMessage.chunk"
    AGENT_MESSAGE_COMPLETE = "agentMessage.complete"
    EXECUTION_STATUS = "executionStatus"
    METADATA = "metadata"
    ERROR = "error"


class TestSuiteEventType(Enum):
    START = "suite.start"
    TEST_START = "suite.test.start"
    TEST_COMPLETE = "suite.test.complete"
    COMPLETE = "suite.complete"
    ERROR = "suite.error"


class TestSuiteRun(CamelCaseModel, table=True):
    __tablename__ : Any = "test_suite_run"
    __table_args__ = (
        Index('ix_test_suite_run_agent_id_executed_at', 'agent_id', 'executed_at'),
    )
    id: int = Field(primary_key=True, default=None)
    agent_id: int = Field(foreign_key="agent.id")
    status: TestSuiteRunStatus = Field(default=TestSuiteRunStatus.RUNNING)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(default=None)
    total_tests: int = Field(default=0)
    passed_tests: int = Field(default=0)
    failed_tests: int = Field(default=0)
    error_tests: int = Field(default=0)
    skipped_tests: int = Field(default=0)


class TestCaseResult(CamelCaseModel, table=True):
    __tablename__ : Any = "test_case_result"
    __table_args__ = (
        Index('ix_test_case_result_test_case_id_executed_at', 'test_case_id', 'executed_at'),
    )
    id: int = Field(primary_key=True, default=None)
    thread_id: Optional[int] = Field(default=None, foreign_key="thread.id")
    test_case_id: int = Field(foreign_key="test_case.thread_id")
    test_suite_run_id: Optional[int] = Field(default=None, foreign_key="test_suite_run.id")
    status: TestCaseResultStatus = Field(default=TestCaseResultStatus.PENDING)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PublicTestCase(CamelCaseModel):
    agent_id: int
    thread: Thread
    last_update: datetime


class NewTestCaseMessage(BaseModel):
    text: str
    origin: ThreadMessageOrigin


class UpdateTestCaseMessage(BaseModel):
    text: str


class UpdateTestCase(BaseModel):
    name: str


class RunTestSuiteRequest(BaseModel):
    test_case_ids: Optional[List[int]] = None
