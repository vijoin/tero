<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue';
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ApiService, Thread, HttpError, TestCase, TestCaseResult, TestCaseResultStatus, TestSuiteRun, TestSuiteRunStatus } from '@/services/api';
import type { TestSuiteExecutionStreamEvent } from '@/services/api';
import AgentTestcasePanel from '@/components/agent/AgentTestcasePanel.vue';
import { useErrorHandler } from '@/composables/useErrorHandler';
import { useToast } from 'vue-toastification';
import ToastMessage from '@/components/common/ToastMessage.vue';

export interface TestCaseExecutionState {
  phase: string;
  userMessage?: { id: number; text: string };
  agentMessage?: { id: number; text: string };
  agentChunks: string;
  status?: TestCaseResultStatus;
  statusUpdates: any[];
}

const { t } = useI18n()
const { handleError } = useErrorHandler()
const toast = useToast()
const api = new ApiService();
const route = useRoute();
const router = useRouter();
const agentId = ref<number>();
const threadId = ref<number>();
const showTestCaseEditor = ref<boolean>(false);
const testCaseId = ref<number>();
const isEditingTestCase = ref<boolean>(false);
const testCases = ref<TestCase[]>([]);
const testCaseResults = ref<TestCaseResult[]>([]);
const latestSuiteRun = ref<TestSuiteRun | undefined>();
const testCasePanel = ref<InstanceType<typeof AgentTestcasePanel>>();
const loadingTests = ref<boolean>(true);
const runningTests = ref<boolean>(false);
const executionStates = ref<Map<number, TestCaseExecutionState>>(new Map());
const testRunStartedByCurrentUser = ref<boolean>(false);
let pollInterval: number | null = null;

const startChat = async () => {
  try {
    const thread = await api.startThread(agentId.value!);
    threadId.value = thread.id;
  } catch (e: unknown) {
    if (e instanceof HttpError && e.status === 400 && e.message.includes("Agent not found")) {
      router.push('/not-found');
    }
  }
};

const handleSelectChat = (chat: Thread) => {
  threadId.value = chat.id;
}

const handleSelectTestCase = (id: number | undefined) => {
  testCaseId.value = id;
}

const handleNewTestCase = (testCase: TestCase) => {
  testCaseId.value = testCase.thread.id;
  testCases.value.push(testCase);
}

const loadTestCases = async (id: number) => {
  try {
    testCases.value = await api.findTestCases(id)
    const suiteRuns = await api.findTestSuiteRuns(id, 1, 0)
    latestSuiteRun.value = suiteRuns.length > 0 ? suiteRuns[0] : undefined
    testCaseResults.value = latestSuiteRun.value ? await api.findTestSuiteRunResults(id, latestSuiteRun.value.id) : []

    if (!testCases.value.length) {
      isEditingTestCase.value = true
    }
    else if (testCaseResults.value.length > 0) {
      handleSelectTestCase(testCases.value[0].thread.id)
      isEditingTestCase.value = false
    }

    if (latestSuiteRun.value && latestSuiteRun.value.status === TestSuiteRunStatus.RUNNING) {
      runningTests.value = true
      startPolling()
    }

  } catch (e) {
    handleError(e)
  } finally {
    loadingTests.value = false
  }
}

const handleDeleteTestCase = (testCaseThreadId: number) => {
  const isSelectedTestCase = testCaseThreadId === testCaseId.value
  testCases.value = testCases.value.filter(tc => tc.thread.id !== testCaseThreadId)
  if (isSelectedTestCase) {
    handleSelectTestCase(undefined)
  }
  if (testCases.value.length === 0 && !isEditingTestCase.value) {
    isEditingTestCase.value = true
  }
}

const startPolling = () => {
  stopPolling()

  pollInterval = window.setInterval(async () => {
    await pollTestSuiteStatus()
  }, 1000)
}

const stopPolling = () => {
  if (pollInterval !== null) {
    window.clearInterval(pollInterval)
    pollInterval = null
  }
}

const pollTestSuiteStatus = async () => {
  if (!agentId.value) return

  try {
    const suiteRuns = await api.findTestSuiteRuns(agentId.value, 1, 0)

    if (suiteRuns.length === 0) {
      stopPolling()
      runningTests.value = false
      return
    }

    latestSuiteRun.value = suiteRuns[0]

    const previousSelectedResult = testCaseId.value
      ? testCaseResults.value.find(tr => tr.testCaseId === testCaseId.value)
      : undefined

    testCaseResults.value = await api.findTestSuiteRunResults(agentId.value, latestSuiteRun.value!.id)

    const currentSelectedResult = testCaseId.value
      ? testCaseResults.value.find(tr => tr.testCaseId === testCaseId.value)
      : undefined

    if (testCaseId.value && currentSelectedResult && previousSelectedResult) {
      const statusChanged = previousSelectedResult.status !== currentSelectedResult.status
      const isNoLongerRunning = currentSelectedResult.status !== TestCaseResultStatus.RUNNING

      if (statusChanged && isNoLongerRunning) {
        await testCasePanel.value?.loadTestCaseData()
      }
    }

    if (latestSuiteRun.value!.status !== TestSuiteRunStatus.RUNNING) {
      stopPolling()
      runningTests.value = false
      testRunStartedByCurrentUser.value = false
    }
  } catch (e) {
    handleError(e)
    stopPolling()
    runningTests.value = false
    testRunStartedByCurrentUser.value = false
  }
}

const processSuiteExecutionStream = async (
  eventStream: AsyncIterable<TestSuiteExecutionStreamEvent>,
  options?: {
    onTestStart?: (testCaseId: number) => void
  }
) => {
  let currentTestCaseId: number | null = null;
  let is409Error = false;

  try {
    for await (const event of eventStream) {
      switch (event.type) {
        case 'suite.start':
          latestSuiteRun.value = {
            id: event.data.suiteRunId,
            agentId: agentId.value!,
            status: TestSuiteRunStatus.RUNNING,
            executedAt: new Date(),
            totalTests: testCases.value.length,
            passedTests: 0,
            failedTests: 0,
            errorTests: 0,
            skippedTests: 0
          }
          break;

        case 'suite.test.start':
          currentTestCaseId = event.data.testCaseId;

          const testCaseResult = testCaseResults.value.find(tr => tr.testCaseId === currentTestCaseId);
          if (testCaseResult) {
            testCaseResult.status = TestCaseResultStatus.RUNNING;
            testCaseResult.id = event.data.resultId;
          }

          executionStates.value.set(currentTestCaseId, {
            phase: 'executing',
            agentChunks: '',
            statusUpdates: []
          });

          if (options?.onTestStart) {
            options.onTestStart(currentTestCaseId);
          }
          break;

        case 'suite.test.metadata':
          const testResult = testCaseResults.value.find(tr => tr.testCaseId === event.data.testCaseId);
          if (testResult) {
            testResult.id = event.data.resultId;
            if (latestSuiteRun.value) {
              testResult.testSuiteRunId = latestSuiteRun.value.id;
            }
          }
          break;

        case 'suite.test.phase':
          const execState = currentTestCaseId ? executionStates.value.get(currentTestCaseId) : null;
          if (execState) {
            execState.phase = event.data.phase;
            if (event.data.phase === 'completed') {
              execState.status = event.data.status as TestCaseResultStatus;
            }
          }
          break;

          case 'suite.test.userMessage':
          const userExecState = currentTestCaseId ? executionStates.value.get(currentTestCaseId) : null;
          if (userExecState) {
            userExecState.userMessage = {
              id: event.data.id,
              text: event.data.text
            }
          }
          break;

          case 'suite.test.agentMessage.start':
          const startExecState = currentTestCaseId ? executionStates.value.get(currentTestCaseId) : null;
          if (startExecState) {
            startExecState.agentMessage = {
              id: event.data.id,
              text: ''
            };
            startExecState.agentChunks = '';
          }
          break;

          case 'suite.test.agentMessage.chunk':
          const chunkExecState = currentTestCaseId ? executionStates.value.get(currentTestCaseId) : null;
          if (chunkExecState) {
            chunkExecState.agentChunks += event.data.chunk;
          }
          break;

        case 'suite.test.agentMessage.complete':
          const completeExecState = currentTestCaseId ? executionStates.value.get(currentTestCaseId) : null;
          if (completeExecState && completeExecState.agentMessage) {
            completeExecState.agentMessage.text = event.data.text;
          }
          break;

        case 'suite.test.executionStatus':
          const statusExecState = currentTestCaseId ? executionStates.value.get(currentTestCaseId) : null;
          if (statusExecState) {
            statusExecState.statusUpdates.push(event.data);
          }
          break;

        case 'suite.test.error':
          if (currentTestCaseId) {
            const errorExecState = executionStates.value.get(currentTestCaseId);
            if (errorExecState) {
              errorExecState.phase = 'completed';
              errorExecState.status = TestCaseResultStatus.ERROR;
            }
            handleTestCaseCompleted(currentTestCaseId, TestCaseResultStatus.ERROR);
          }
          break;

        case 'suite.test.complete':
          const completedTestCaseId = event.data.testCaseId;
          handleTestCaseCompleted(completedTestCaseId, event.data.status as TestCaseResultStatus);
          executionStates.value.delete(completedTestCaseId);
          break;

        case 'suite.error':
          toast.error(
            { component: ToastMessage, props: { message: t('suiteExecutionFailed') } },
            { timeout: 5000, icon: false }
          );

          testCaseResults.value.forEach(result => {
            if (result.status === TestCaseResultStatus.RUNNING || result.status === TestCaseResultStatus.PENDING) {
              result.status = TestCaseResultStatus.SKIPPED;
            }
          });

          executionStates.value = new Map();
          break;

        case 'suite.complete':
          if (latestSuiteRun.value) {
            latestSuiteRun.value.status = event.data.status as TestSuiteRunStatus
            latestSuiteRun.value.completedAt = new Date()
            latestSuiteRun.value.passedTests = event.data.passed
            latestSuiteRun.value.failedTests = event.data.failed
            latestSuiteRun.value.errorTests = event.data.errors
            latestSuiteRun.value.skippedTests = event.data.skipped
          }
          break;
      }
    }
  } catch (error) {
     if (error instanceof HttpError && error.status === 409) {
       is409Error = true;
       toast.info(
         { component: ToastMessage, props: { message: t('suiteAlreadyRunning') } },
         { timeout: 5000, icon: false }
       )
       testRunStartedByCurrentUser.value = false
       startPolling()
    } else {
      if (currentTestCaseId) {
        const testCaseResult = testCaseResults.value.find(tr => tr.testCaseId === currentTestCaseId);
        if (testCaseResult) {
          testCaseResult.status = TestCaseResultStatus.ERROR;
        }
        const execState = executionStates.value.get(currentTestCaseId);
        if (execState) {
          execState.phase = 'completed';
          execState.status = TestCaseResultStatus.ERROR;
        }
      }
      handleError(error)
    }
  } finally {
    executionStates.value.clear();
    if (!is409Error) {
      runningTests.value = false;
      testRunStartedByCurrentUser.value = false;
    }
  }
}

const handleRunTests = async () => {
  isEditingTestCase.value = false
  runningTests.value = true
  testRunStartedByCurrentUser.value = true

  testCaseResults.value = testCases.value.map(testCase => {
    return new TestCaseResult(
      testCase.thread.id,
      new Date(),
      TestCaseResultStatus.PENDING
    )
  })

  await processSuiteExecutionStream(api.runTestSuiteStream(agentId.value!))
}

const handleTestCaseCompleted = (completedTestCaseId: number, status: TestCaseResultStatus) => {
  const result = testCaseResults.value.find(tr => tr.testCaseId === completedTestCaseId)
  if (result) {
    result.status = status
  }
}

const handleRunSingleTest = async (singleTestCaseId: number) => {
  isEditingTestCase.value = false
  runningTests.value = true
  testRunStartedByCurrentUser.value = true

  testCaseResults.value = testCases.value.map(testCase => {
    return new TestCaseResult(
      testCase.thread.id,
      new Date(),
      testCase.thread.id === singleTestCaseId ? TestCaseResultStatus.PENDING : TestCaseResultStatus.SKIPPED
    )
  })

  await processSuiteExecutionStream(api.runTestSuiteStream(agentId.value!, [singleTestCaseId]), {
    onTestStart: (testCaseId) => {
      handleSelectTestCase(testCaseId)
    }
  })
}

onMounted(async () => {
  agentId.value = parseInt(route.params.agentId as string);
  await startChat();
  if (agentId.value) {
    await loadTestCases(agentId.value);
  }
});

onBeforeRouteUpdate(async (to) => {
  stopPolling();
  runningTests.value = false;
  testRunStartedByCurrentUser.value = false;

  agentId.value = parseInt(to.params.agentId as string);
  await startChat();
  if (agentId.value) {
    await loadTestCases(agentId.value);
  }
});

onBeforeUnmount(() => {
  stopPolling();
});
</script>

<template>
  <PageLayout left-column-class="w-[calc(40%-var(--spacing)*3/2)] min-w-[670px]"
    right-column-class="w-[calc(60%-var(--spacing)*3/2)]">
    <template #left>
      <AgentEditorPanel v-if="threadId" :selected-thread-id="threadId" :selected-test-case-id="testCaseId"
        :test-cases="testCases" @select-test-case="handleSelectTestCase" @show-test-case-editor="showTestCaseEditor = $event"
        :loading-tests="loadingTests" @editing-testcase="isEditingTestCase = $event" :editing-testcase="isEditingTestCase"
        @import-agent="loadTestCases(agentId!)"
        @delete-test-case="handleDeleteTestCase" :test-case-results="testCaseResults" :running-tests="runningTests" @run-tests="handleRunTests"
        @run-single-test="handleRunSingleTest" @new-test-case="handleNewTestCase" :test-suite-run="latestSuiteRun" />
    </template>
    <template #right>
      <ChatPanel :thread-id="threadId" v-if="threadId && !showTestCaseEditor" :editing-agent="true" @new-chat="startChat"
        @select-chat="handleSelectChat" />
      <AgentTestcasePanel v-if="agentId && showTestCaseEditor" :test-case-id="testCaseId" :agent-id="agentId"
        :thread-id="threadId" :is-editing="isEditingTestCase" @new-test-case="handleNewTestCase" :test-cases="testCases" @cancel-edit="isEditingTestCase = false"
        :is-new-test-case="testCases.length === 0" :test-case-results="testCaseResults" ref="testCasePanel"
        :test-case="testCases.find(tc => tc.thread.id === testCaseId)"
        :test-case-result="testCaseResults.find(tr => tr.testCaseId === testCaseId)"
        :execution-state="testCaseId ? executionStates.get(testCaseId) : undefined" />
    </template>
  </PageLayout>
</template>

<i18n lang="json">{
  "en": {
    "suiteExecutionFailed": "Test suite execution failed",
    "suiteAlreadyRunning": "Please wait for the test suite to finish running before starting a new execution"
  },
  "es": {
    "suiteExecutionFailed": "Falló la ejecución de la suite de tests",
    "suiteAlreadyRunning": "Espera a que el test suite termine de correr para lanzar una nueva ejecucion"
  }
}</i18n>
