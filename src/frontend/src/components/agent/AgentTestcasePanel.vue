<script setup lang="ts">
import { TestCase, ThreadMessage, ThreadMessageOrigin, TestCaseResult, TestCaseResultStatus } from '@/services/api';
import { useI18n } from 'vue-i18n';
import { onMounted, ref, watch, computed, nextTick } from 'vue';
import { ApiService, HttpError } from '@/services/api';
import { AgentTestcaseChatUiMessage } from './AgentTestcaseChatMessage.vue';
import ChatInput from '../../../../common/src/components/chat/ChatInput.vue';
import { useErrorHandler } from '@/composables/useErrorHandler';
import TestCaseStatus from './TestCaseStatus.vue';
import { AnimationEffect } from '../../../../common/src/utils/animations';
import type { TestCaseExecutionState } from '@/pages/AgentEditorPage.vue';
const api = new ApiService()

const { t } = useI18n()
const { handleError } = useErrorHandler()

const props = defineProps<{
    agentId: number,
    threadId?: number,
    testCaseId?: number,
    isEditing?: boolean,
    isNewTestCase?: boolean,
    testCase?: TestCase,
    testCaseResult?: TestCaseResult,
    executionState?: TestCaseExecutionState
}>()

const emit = defineEmits<{
    (e: 'newTestCase', testCase: TestCase): void
    (e: 'cancelEdit'): void
}>()

const messages = ref<AgentTestcaseChatUiMessage[]>([])
const inputText = ref('')
const selectedMessage = ref<AgentTestcaseChatUiMessage | undefined>()
const chatInputRef = ref<InstanceType<typeof ChatInput>>()
const isRunning = computed(() => {
    if (props.executionState) {
        return props.executionState.phase === 'executing' || props.executionState.phase === 'evaluating'
    }
    return props.testCaseResult?.status === TestCaseResultStatus.RUNNING
})
const isLoading = ref(false)

onMounted(async () => {
    isLoading.value = true
    try {
        if (props.testCaseId) {
            await loadTestCaseData()
        } else if (props.isNewTestCase) {
            messages.value = [
                new AgentTestcaseChatUiMessage(t('userMessagePlaceholder'), true, true),
                new AgentTestcaseChatUiMessage(t('agentMessagePlaceholder'), false, true),
            ]
            await selectLastMessageOrPlaceholder()
        }
    } finally {
        isLoading.value = false
    }
})

const loadTestCaseData = async () => {
    if (props.testCaseId) {
        isLoading.value = true
        try {
            if (props.isEditing) {
                try {
                    messages.value = mapMessagesToAgentTestcaseChatUi(await api.findTestCaseMessages(props.agentId, props.testCaseId))
                } catch (error) {
                    handleError(error)
                }
                await selectLastMessageOrPlaceholder()
            } else {
                try {
                  if (props.testCaseResult?.testSuiteRunId && props.testCaseResult?.id) {
                        messages.value = mapMessagesToAgentTestcaseChatUi(
                            await api.findTestSuiteRunResultMessages(
                                props.agentId,
                                props.testCaseResult.testSuiteRunId,
                                props.testCaseResult.id
                            ),
                            false
                        )
                    } else {
                        messages.value = []
                    }
                } catch (error) {
                    if (error instanceof HttpError && error.status === 404) {
                        messages.value = []
                    } else {
                        handleError(error)
                    }
                }
            }
        } finally {
            isLoading.value = false
        }
    }
}

const mapMessagesToAgentTestcaseChatUi = (msgs: ThreadMessage[], usePlaceholders: boolean = true): AgentTestcaseChatUiMessage[] => {
    const first = msgs[0];
    const second = msgs[1];

    return [
        ...(first || usePlaceholders ? [new AgentTestcaseChatUiMessage(
            first?.text || t('userMessagePlaceholder'),
            true,
            !first?.text,
            first?.id
        )] : []),
        ...(second || usePlaceholders ? [new AgentTestcaseChatUiMessage(
            second?.text || t('agentMessagePlaceholder'),
            false,
            !second?.text,
            second?.id
        )] : []),
    ];
}

const handleSelectMessage = async (message: AgentTestcaseChatUiMessage) => {
    selectedMessage.value = message
    await nextTick()
    chatInputRef.value?.focus()
    inputText.value = message.isPlaceholder ? '' : message.text
}

const handleSelectTestCase = async (testCaseId: number | undefined) => {
    if (testCaseId) {
        if(!isRunning.value) await loadTestCaseData()
        if(props.isEditing) await selectLastMessageOrPlaceholder()
    } else if (props.isNewTestCase) {
        inputText.value = ''
        messages.value = [
            new AgentTestcaseChatUiMessage(t('userMessagePlaceholder'), true, true),
            new AgentTestcaseChatUiMessage(t('agentMessagePlaceholder'), false, true),
        ]
        await selectLastMessageOrPlaceholder()
    }
}

watch(() => props.testCaseId, async (newVal) => {
    await handleSelectTestCase(newVal)
})

watch([() => props.isEditing, () => props.isNewTestCase], async () => {
    await handleSelectTestCase(props.testCaseId)
})

watch(() => props.executionState, (newState, oldState) => {
    if (!newState) {
        return
    }

    if (newState.phase === 'executing') {
        messages.value = []
    }

    if (newState.userMessage) {
        let userMsg = messages.value.find(m => m.isUser)
        if (!userMsg) {
            userMsg = new AgentTestcaseChatUiMessage(
                newState.userMessage.text,
                true,
                false,
                newState.userMessage.id
            )
            messages.value.push(userMsg)
        } else {
            userMsg.text = newState.userMessage.text
            userMsg.id = newState.userMessage.id
        }
    }

    if (newState.agentChunks || newState.agentMessage) {
        const agentText = newState.agentChunks || newState.agentMessage?.text || ''
        let agentMsg = messages.value.find(m => !m.isUser)

        if (!agentMsg) {
            agentMsg = new AgentTestcaseChatUiMessage(
                agentText,
                false,
                false,
                newState.agentMessage?.id
            )
            messages.value.push(agentMsg)
        } else {
            agentMsg.text = agentText
            agentMsg.id = newState.agentMessage?.id
        }

        agentMsg.isStreaming = newState.phase === 'executing'

        if (newState.statusUpdates && newState.statusUpdates.length > 0) {
            agentMsg.statusUpdates = newState.statusUpdates.map((su: any) => ({
                action: su.action,
                toolName: su.toolName,
                description: su.description,
                args: su.args,
                step: su.step,
                result: su.result,
                timestamp: su.timestamp || new Date()
            }))
        }

        if (newState.phase === 'completed') {
            agentMsg.completeStatus()
            agentMsg.isStreaming = false
        }
    }
}, { deep: true })

const onMessageSend = async () => {
    if (!selectedMessage.value) return

    selectedMessage.value.text = inputText.value
    inputText.value = ''
    let testCase = props.testCase || null;
    if (!testCase) {
        testCase = await api.addTestCase(props.agentId)
        emit('newTestCase', testCase)
    }
    let updatedMessage: ThreadMessage;
    if (selectedMessage.value.id) {
        updatedMessage = await api.updateTestCaseMessage(props.agentId, testCase.thread.id, selectedMessage.value.id, {
            text: selectedMessage.value.text,
        })
    } else {
        updatedMessage = await api.addTestCaseMessage(props.agentId, testCase.thread.id, { text: selectedMessage.value.text, origin: selectedMessage.value.isUser ? ThreadMessageOrigin.USER : ThreadMessageOrigin.AGENT })
    }
    selectedMessage.value.id = updatedMessage.id
    selectedMessage.value.isPlaceholder = false
    if(getLastPlaceholder()) await selectLastMessageOrPlaceholder()
    else selectedMessage.value = undefined
}

const selectLastMessageOrPlaceholder = async () => {
    selectedMessage.value = getLastPlaceholder() || messages.value[messages.value.length - 1]
    inputText.value = selectedMessage.value?.isPlaceholder ? '' : selectedMessage.value?.text || ''
    if (selectedMessage.value) {
        await nextTick()
        chatInputRef.value?.focus()
    }
}

const getLastPlaceholder = () => {
    return messages.value.find(m => m.isPlaceholder)
}

const isMessageSelectable = (message: AgentTestcaseChatUiMessage) => {
    return getLastPlaceholder()?.uuid === message.uuid
}

const statusDescription = computed(() => {
    switch (props.testCaseResult?.status) {
        case TestCaseResultStatus.SUCCESS:
            return t('successDescription')
        case TestCaseResultStatus.FAILURE:
            return t('failureDescription')
        case TestCaseResultStatus.ERROR:
            return t('errorDescription')
        default:
            return ''
    }
})

defineExpose({
    loadTestCaseData
})
</script>

<template>
    <Animate v-if="isLoading" :effect="AnimationEffect.FADE_IN" class="h-full">
        <AgentTestcasePanelSkeleton />
    </Animate>
    <FlexCard v-else header-height="auto">
        <template #header>
            <div class="flex flex-row items-center gap-4 h-10">
              <SimpleButton v-if="isEditing && testCase" @click="$emit('cancelEdit')">
                  <IconArrowLeft />
              </SimpleButton>
              <div v-if="isEditing" class="flex flex-row gap-2">
                  <IconPencil v-if="testCase?.thread.name"/>
                  {{ testCase?.thread.name ? t('editTestCaseTitle', { testCaseName: testCase?.thread.name }) :
                      t('newTestCaseTitle') }}
              </div>
              <div v-else class="flex gap-2">
                  <IconLoader2 v-if="isRunning" class="text-light-gray animate-spin" />
                  <IconPlayerPlay v-else-if="testCaseResult"/>
                  {{ testCaseResult ? isRunning ? t('runningTestCase', { testCaseName: testCase?.thread.name }) : t('testCaseResult', { testCaseName: testCase?.thread.name }) : t('noRunResults') }}
              </div>
            </div>
        </template>
        <div class="max-w-[837px] mx-auto flex-1 w-full min-h-0">
            <div class="flex flex-col h-full gap-4 py-4">
                <div v-if="!isEditing && !testCaseResult && !executionState">
                    {{ testCaseId ? t('noTestCaseResultsDescription') : t('noRunResultsDescription') }}
                </div>

                <div class="flex flex-1 min-h-0 gap-2 w-full overflow-y-auto">
                    <div v-if="messages.length > 0 && (isEditing || (testCaseResult?.status !== TestCaseResultStatus.ERROR && testCaseResult?.status !== TestCaseResultStatus.PENDING))" class="flex flex-col w-full">
                        <div v-for="(message, index) in messages" :key="message.uuid">
                            <div v-if="!message.isUser && message.statusUpdates.length > 0" class="px-2 py-3">
                                <ChatStatus :status-updates="message.statusUpdates" :is-complete="message.isStatusComplete" />
                            </div>
                            <AgentTestcaseChatMessage :message="message"
                                :actions-enabled="!message.isPlaceholder && isEditing"
                                :is-selected="selectedMessage?.uuid === message.uuid" @select="handleSelectMessage"
                                :selectable="isMessageSelectable(message)" />
                        </div>
                    </div>
                </div>
                <div v-if="isEditing && selectedMessage"
                    class="flex flex-col gap-1 p-3 relative rounded-xl border border-auxiliar-gray focus-within:border-abstracta bg-white shadow-sm"
                    :class="selectedMessage ? selectedMessage?.isUser ? '!border-primary' : '!border-info' : ''">
                    <span class="absolute top-[-.85rem] right-20 font-semibold rounded-full px-4 py-1 text-sm z-10"
                        :class="{ 'bg-abstracta text-white': selectedMessage?.isUser, 'bg-info text-white': !selectedMessage?.isUser }">
                        {{ selectedMessage?.isUser ? t('user') : t('agent') }}</span>
                    <ChatInput
                        v-model="inputText"
                        ref="chatInputRef"
                        :chat="{
                            supportsStopResponse: () => false,
                            findPrompts: async () => [],
                            savePrompt: async () => {},
                            deletePrompt: async (id: number) => {},
                            supportsFileUpload: () => false,
                            supportsTranscriptions: () => false,
                            transcribe: async (blob: Blob) => '',
                            handleError: handleError
                        }"
                        :borderless="true"
                        @send="onMessageSend">
                    </ChatInput>
                </div>
                <div v-else-if="!isEditing && (testCaseResult || executionState)"
                    class="h-35 min-h-35 flex-shrink-0 border-t-1 border-auxiliar-gray p-4 overflow-y-auto">
                    <div class="flex flex-col gap-4">
                        <TestCaseStatus v-if="!isRunning && testCaseResult" :status="testCaseResult.status" />
                        <div v-if="executionState && (executionState.phase === 'executing' || executionState.phase === 'evaluating')" class="flex flex-row items-center gap-2">
                            <IconLoader2 class="text-light-gray animate-spin" />
                            <span v-if="executionState.phase === 'executing'">{{ t('phaseExecuting') }}</span>
                            <span v-else>{{ t('phaseEvaluating') }}</span>
                        </div>
                        <div v-else-if="isRunning" class="flex flex-row items-center gap-2">
                            <IconLoader2 class="text-light-gray animate-spin" />
                            <span>{{ t('testRunning') }}</span>
                        </div>
                        <div v-else-if="testCaseResult" class="flex flex-row items-center gap-2">
                            {{ statusDescription }}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </FlexCard>
</template>

<i18n lang="json">{
    "en": {
        "newTestCaseTitle": "Create a new test case",
        "editTestCaseTitle": "Editing: {testCaseName}",
        "userMessagePlaceholder": "Message that a person would send to the agent…",
        "agentMessagePlaceholder": "Expected response from the agent…",
        "user": "Message from the user",
        "agent": "Expected response",
        "noRunResults": "No execution results yet",
        "successDescription": "The agent's response matched the expected output. No formatting or content deviations were detected.",
        "failureDescription": "The agent's response did not match the expected output. Formatting or content deviations were detected.",
        "errorDescription": "An error occurred while running the test case",
        "noRunResultsDescription": "Run the full suite to validate all defined test cases.",
        "noTestCaseResultsDescription": "Run the test to compare the agent's response with the expected output.",
        "obtainedResultLabel": "Obtained result",
        "runningTestCase": "Running: {testCaseName}",
        "testCaseResult": "Test case result: {testCaseName}",
        "testRunning": "Test is running...",
        "phaseExecuting": "Executing test case...",
        "phaseEvaluating": "Evaluating response..."
    },
    "es": {
        "newTestCaseTitle": "Crea un nuevo test case",
        "editTestCaseTitle": "Editando: {testCaseName}",
        "userMessagePlaceholder": "Mensaje que enviaría una persona al agente…",
        "agentMessagePlaceholder": "Respuesta esperada del agente…",
        "user": "Mensaje del usuario",
        "agent": "Respuesta esperada",
        "noRunResults": "No hay resultados de ejecución aún",
        "successDescription": "La respuesta del agente coincidió con la salida esperada. No se detectaron desvíos de formato o contenido.",
        "failureDescription": "La respuesta del agente no coincidió con la salida esperada. Se detectaron desvíos de formato o contenido.",
        "errorDescription": "Ocurrió un error al ejecutar el test case",
        "noRunResultsDescription": "Corre la suite completa para validar todos los test cases definidos.",
        "noTestCaseResultsDescription": "Ejecuta el test para comparar la respuesta del agente con la esperada.",
        "obtainedResultLabel": "Resultado obtenido",
        "runningTestCase": "Ejecutando: {testCaseName}",
        "testCaseResult": "Resultado del test case: {testCaseName}",
        "testRunning": "El test está ejecutándose...",
        "phaseExecuting": "Ejecutando test case...",
        "phaseEvaluating": "Evaluando respuesta..."
    }
}</i18n>
