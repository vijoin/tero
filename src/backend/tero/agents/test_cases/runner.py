import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import List, cast, Any, AsyncIterator, Tuple

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages.ai import UsageMetadata
from langchain_core.outputs import LLMResult
from langchain_core.prompts import ChatPromptTemplate
from openevals.llm import create_async_llm_as_judge
from openevals.types import EvaluatorResult
from sqlmodel.ext.asyncio.session import AsyncSession
from sse_starlette.event import ServerSentEvent

from ...core.env import env
from ...ai_models import ai_factory
from ...ai_models.repos import AiModelRepository
from ...ai_models.domain import LlmModel
from ...usage.domain import MessageUsage
from ...threads.domain import ThreadMessage, Thread, ThreadMessageOrigin, AgentMessageEvent, AgentActionEvent
from ...threads.repos import ThreadMessageRepository, ThreadRepository
from ...threads.engine import AgentEngine
from ...usage.repos import UsageRepository
from ...core.repos import engine
from ..domain import Agent
from .domain import TestCase, TestCaseResultStatus, TestCaseEventType, TestCaseResult, TestSuiteRun, TestSuiteEventType, TestSuiteRunStatus
from .repos import TestCaseResultRepository, TestSuiteRunRepository

logger = logging.getLogger(__name__)

TEST_CASE_EVALUATOR_PROMPT = ChatPromptTemplate(
    [
        ("system", "You are an expert evaluator assessing whether the actual output from an AI agent matches the expected output for a given test case."),
        ("human", """
Compare the actual output with the expected output based on these criteria:
1. Semantic equivalence - Does the actual output convey the same meaning as the expected output?
2. Completeness - Does the actual output contain all key information from the expected output?
3. Accuracy - Is the actual output factually correct when compared to the expected output?
4. Relevance - Does the actual output appropriately address the input?
5. Conciseness - Does the actual output avoid including extra information not present in the expected output? If the expected output is concise the response should also be concise for example if the expected output is "Agent response" the actual output should also be "Agent response" or similar.

Be lenient with minor differences in wording, formatting, or style. Focus on whether the core meaning and key information match. Be strict about factual errors, missing critical information, or extraneous details that go beyond the expected output.

Respond with 'Y' if the actual output sufficiently matches the expected output, or 'N' if there are significant discrepancies. Then provide a brief explanation.


Input:
{{inputs}}

Expected Output:
{{reference_outputs}}

Actual Output:
{{outputs}}

""")],
    template_format="mustache"
)


class EvaluatorUsageTrackingCallback(AsyncCallbackHandler):
    def __init__(self, usage: MessageUsage, model: LlmModel):
        self.usage = usage
        self.model = model

    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
         # Try to extract usage from llm_output first (most common format)
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage')
            if token_usage:
                self.usage.increment_with_metadata(UsageMetadata(
                    input_tokens=token_usage.get('prompt_tokens', 0),
                    output_tokens=token_usage.get('completion_tokens', 0),
                    total_tokens=token_usage.get('total_tokens', 0)
                ), self.model)
                return
        
        # Fallback: try to extract from generation_info
        if response.generations:
            for generation_list in response.generations:
                for generation in generation_list:
                    if hasattr(generation, 'generation_info') and generation.generation_info:
                        token_usage = generation.generation_info.get('token_usage')
                        if token_usage:
                            self.usage.increment_with_metadata(UsageMetadata(
                                input_tokens=token_usage.get('prompt_tokens', 0),
                                output_tokens=token_usage.get('completion_tokens', 0),
                                total_tokens=token_usage.get('total_tokens', 0)
                            ), self.model)
                            return


class TestCaseRunner:

    def __init__(self, db: AsyncSession):
        self._db = db
    
    async def run_test_case_stream(self, test_case: TestCase, agent: Agent, user_id: int, result: TestCaseResult) -> AsyncIterator[Tuple[TestCaseEventType, Any]]:
        results_repo = TestCaseResultRepository(self._db)
        try:
            messages = await ThreadMessageRepository(self._db).find_by_thread_id(test_case.thread_id)

            if not messages:
                result.status = TestCaseResultStatus.SKIPPED
                result = await results_repo.save(result)

                yield (TestCaseEventType.METADATA, {
                    "testCaseId": test_case.thread_id,
                    "resultId": result.id,
                })

                yield (TestCaseEventType.PHASE, {
                    "phase": "completed",
                    "status": TestCaseResultStatus.SKIPPED.value,
                    "evaluation": None
                })
                return

            execution_thread = await ThreadRepository(self._db).add(Thread(
                agent_id=agent.id,
                user_id=user_id,
                is_test_case=True
            ))

            result.thread_id = execution_thread.id
            result.status = TestCaseResultStatus.RUNNING
            result = await results_repo.save(result)

            yield (TestCaseEventType.METADATA, {
                "testCaseId": test_case.thread_id,
                "resultId": result.id,
            })

            user_input = messages[0].text
            expected_output = messages[1].text if len(messages) > 1 else ""

            yield (TestCaseEventType.PHASE, {"phase": "executing"})

            actual_output = ""

            async for event_type, content in self._execute_agent_with_input_stream(agent, user_input, user_id, execution_thread.id):
                if event_type == TestCaseEventType.AGENT_MESSAGE_COMPLETE:
                    actual_output += content["text"]
                    yield (event_type, content)
                elif event_type in [TestCaseEventType.USER_MESSAGE, TestCaseEventType.AGENT_MESSAGE_START,
                                    TestCaseEventType.AGENT_MESSAGE_CHUNK, TestCaseEventType.EXECUTION_STATUS]:
                    yield (event_type, content)

            yield (TestCaseEventType.PHASE, {"phase": "evaluating"})

            evaluation_result = await self._evaluate_test_case_result(
                user_input, expected_output, actual_output, user_id, agent
            )

            final_status = TestCaseResultStatus.SUCCESS if evaluation_result else TestCaseResultStatus.FAILURE

            result.status = final_status
            await results_repo.save(result)

            yield (TestCaseEventType.PHASE, {
                "phase": "completed",
                "status": final_status.value,
                "evaluation": {
                    "passed": evaluation_result,
                }
            })

        except Exception:
            logger.exception(f"Unexpected error running test case {test_case.thread_id}")
            try:
                result.status = TestCaseResultStatus.ERROR
                await results_repo.save(result)
            except Exception:
                pass
            yield (TestCaseEventType.PHASE, {
                "phase": "completed",
                "status": TestCaseResultStatus.ERROR.value,
                "evaluation": None
            })
    
    async def _execute_agent_with_input_stream(self, agent: Agent, user_input: str, user_id: int, thread_id: int) -> AsyncIterator[Tuple[TestCaseEventType, Any]]:
        thread_message_repo = ThreadMessageRepository(self._db)
        input_message = await thread_message_repo.add(ThreadMessage(
            text=user_input,
            origin=ThreadMessageOrigin.USER,
            timestamp=datetime.now(timezone.utc),
            thread_id=thread_id
        ))
        
        yield (TestCaseEventType.USER_MESSAGE, {
            "id": input_message.id,
            "text": input_message.text,
        })
        
        input_message_usage = MessageUsage(user_id=user_id, agent_id=agent.id, model_id=agent.model_id, message_id=input_message.id)
        engine = AgentEngine(agent, user_id, self._db)
        
        response_message = await thread_message_repo.add(ThreadMessage(
            text="", 
            origin=ThreadMessageOrigin.AGENT,
            timestamp=datetime.now(timezone.utc),
            thread_id=thread_id,
            parent_id=input_message.id
        ))

        yield (TestCaseEventType.AGENT_MESSAGE_START, {
            "id": response_message.id
        })
        
        complete_response = ""
        async for event in engine.answer([input_message], input_message_usage, asyncio.Event()):
            if isinstance(event, AgentActionEvent):
                yield (TestCaseEventType.EXECUTION_STATUS, event)
            elif isinstance(event, AgentMessageEvent):
                complete_response += event.content
                yield (TestCaseEventType.AGENT_MESSAGE_CHUNK, {
                    "id": response_message.id,
                    "chunk": event.content
                })
        
        response_message.text = complete_response
        response_message.timestamp = datetime.now(timezone.utc)
        await thread_message_repo.update(response_message)
        await UsageRepository(self._db).add(input_message_usage)
        
        yield (TestCaseEventType.AGENT_MESSAGE_COMPLETE, {
            "id": response_message.id,
            "text": complete_response,
        })
    
    async def _evaluate_test_case_result(
        self, 
        user_input: str, 
        expected_output: str, 
        actual_output: str,
        user_id: int,
        agent: Agent,
    ) -> bool:
        ai_model_repo = AiModelRepository(self._db)
        evaluator_model = cast(LlmModel, await ai_model_repo.find_by_id(cast(str, env.internal_evaluator_model)))
 
        evaluator_usage = MessageUsage(user_id=user_id, agent_id=agent.id, model_id=evaluator_model.id, message_id=None)
        usage_callback = EvaluatorUsageTrackingCallback(evaluator_usage, evaluator_model)
        
        judge_llm = ai_factory.build_chat_model(
            evaluator_model.id,
            temperature=env.internal_evaluator_temperature
        )
        judge_llm.callbacks.append(usage_callback)
        
        evaluator = create_async_llm_as_judge(
            prompt=TEST_CASE_EVALUATOR_PROMPT,
            judge=judge_llm,
        )
        
        evaluation_result = await evaluator(
            inputs=user_input,
            outputs=actual_output,
            reference_outputs=expected_output
        )
        
        await UsageRepository(self._db).add(evaluator_usage)
        
        result_obj = cast(EvaluatorResult, evaluation_result)
        return cast(bool, result_obj.get("score"))

    async def run_test_suite_stream(
        self,
        agent: Agent,
        all_test_cases: List[TestCase],
        test_cases_to_run: List[TestCase],
        user_id: int,
        suite_run: TestSuiteRun,
    ) -> AsyncIterator[bytes]:
        suite_repo = TestSuiteRunRepository(self._db)
        results_repo = TestCaseResultRepository(self._db)

        try:
            test_case_ids_to_run = {tc.thread_id for tc in test_cases_to_run}

            pending_results: dict[int, TestCaseResult] = {}
            for test_case in all_test_cases:
                if test_case.thread_id in test_case_ids_to_run:
                    pending_result = await results_repo.save(TestCaseResult(
                        test_case_id=test_case.thread_id,
                        test_suite_run_id=suite_run.id,
                        status=TestCaseResultStatus.PENDING
                    ))
                    pending_results[test_case.thread_id] = pending_result
                else:
                    await results_repo.save(TestCaseResult(
                        test_case_id=test_case.thread_id,
                        test_suite_run_id=suite_run.id,
                        status=TestCaseResultStatus.SKIPPED
                    ))

            yield ServerSentEvent(event=TestSuiteEventType.START.value, data=json.dumps({
                "suiteRunId": suite_run.id
            })).encode()

            passed = 0
            failed = 0
            errors = 0
            skipped = len(all_test_cases) - len(test_cases_to_run)

            for test_case in test_cases_to_run:
                result = pending_results[test_case.thread_id]
                yield ServerSentEvent(event=TestSuiteEventType.TEST_START.value, data=json.dumps({
                    "testCaseId": test_case.thread_id,
                    "resultId": result.id
                })).encode()

                async for event_type, content in self.run_test_case_stream(
                    test_case, agent, user_id, pending_results[test_case.thread_id]
                ):
                    if event_type == TestCaseEventType.PHASE and content.get("phase") == "completed":
                        status_value = content.get("status")
                        if status_value == TestCaseResultStatus.SUCCESS.value:
                            passed += 1
                        elif status_value == TestCaseResultStatus.FAILURE.value:
                            failed += 1
                        elif status_value == TestCaseResultStatus.SKIPPED.value:
                            skipped += 1
                        else:
                            errors += 1

                    yield ServerSentEvent(event=f"suite.test.{event_type.value}", data=json.dumps(content.model_dump() if event_type == TestCaseEventType.EXECUTION_STATUS else content)).encode()

                yield ServerSentEvent(event=TestSuiteEventType.TEST_COMPLETE.value, data=json.dumps({
                    "testCaseId": test_case.thread_id,
                    "resultId": result.id,
                    "status": result.status.value
                })).encode()

            suite_run.completed_at = datetime.now(timezone.utc)
            suite_run.total_tests = len(all_test_cases)
            suite_run.passed_tests = passed
            suite_run.failed_tests = failed
            suite_run.error_tests = errors
            suite_run.skipped_tests = skipped
            suite_run.status = TestSuiteRunStatus.FAILURE if errors > 0 or failed > 0 else TestSuiteRunStatus.SUCCESS

            suite_run = await suite_repo.save(suite_run)

            yield ServerSentEvent(event=TestSuiteEventType.COMPLETE.value, data=json.dumps({
                "suiteRunId": suite_run.id,
                "status": suite_run.status.value,
                "totalTests": suite_run.total_tests,
                "passed": suite_run.passed_tests,
                "failed": suite_run.failed_tests,
                "errors": suite_run.error_tests,
                "skipped": suite_run.skipped_tests
            })).encode()

        except Exception:
            logger.exception(f"Error streaming test suite for agent {agent.id}")
            await cleanup_orphaned_suite_run(suite_run.id, agent.id)
            suite_run.status = TestSuiteRunStatus.FAILURE
            suite_run.completed_at = datetime.now(timezone.utc)
            suite_run = await suite_repo.save(suite_run)
            yield ServerSentEvent(event=TestSuiteEventType.ERROR.value, data=json.dumps({})).encode()


# Cleanup running or pending results for a suite in case of suite error or connection closed
# Has its own db session to be able to run on a background task
async def cleanup_orphaned_suite_run(suite_run_id: int, agent_id: int):
    async with AsyncSession(engine, expire_on_commit=False) as db:
        try:
            results_repo = TestCaseResultRepository(db)
            suite_repo = TestSuiteRunRepository(db)
            
            current_suite = await suite_repo.find_by_id_and_agent_id(suite_run_id, agent_id)
            if not current_suite or current_suite.status != TestSuiteRunStatus.RUNNING:
                return
            
            all_results = await results_repo.find_by_suite_run_id(suite_run_id)
            for result in all_results:
                if result.status in [TestCaseResultStatus.PENDING, TestCaseResultStatus.RUNNING]:
                    result.status = TestCaseResultStatus.SKIPPED
                    db.add(result)
            
            current_suite.status = TestSuiteRunStatus.FAILURE
            current_suite.completed_at = datetime.now(timezone.utc)
            
            current_suite.error_tests = sum(1 for r in all_results if r.status == TestCaseResultStatus.ERROR)
            current_suite.passed_tests = sum(1 for r in all_results if r.status == TestCaseResultStatus.SUCCESS)
            current_suite.failed_tests = sum(1 for r in all_results if r.status == TestCaseResultStatus.FAILURE)
            current_suite.skipped_tests = sum(1 for r in all_results if r.status == TestCaseResultStatus.SKIPPED)
            
            db.add(current_suite)
            
            await db.commit()
            
        except Exception as error:
            logger.exception(f"Error during background cleanup for suite {suite_run_id}: {error}")
            try:
                await db.rollback()
            except:
                pass
