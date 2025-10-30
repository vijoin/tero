<script lang="ts" setup>
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, onBeforeRouteUpdate, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Agent, ApiService, LlmModel, LlmTemperature, ReasoningEffort, LlmModelType, AgentToolConfig, AutomaticAgentField, Team, TestCase, TestCaseResult, TestCaseResultStatus, TestSuiteRun, TestSuiteRunStatus, LlmModelVendor } from '@/services/api'
import { IconPlayerPlay, IconPencil, IconTrash, IconDownload, IconUpload } from '@tabler/icons-vue'
import TestCaseStatus from './TestCaseStatus.vue'
import { AnimationEffect } from '../../../../common/src/utils/animations'
import { useErrorHandler } from '@/composables/useErrorHandler'
import { useAgentStore } from '@/composables/useAgentStore'
import { useAgentPromptStore } from '@/composables/useAgentPromptStore'
import { loadUserProfile } from '@/composables/useUserProfile'
import { AgentPrompt, UploadedFile } from '../../../../common/src/utils/domain'
import moment from 'moment'
import openAiIcon from '@/assets/images/open-ai.svg'
import googleIcon from '@/assets/images/gemini.svg'
import anthropicIcon from '@/assets/images/anthropic.svg'


const props = defineProps<{
  selectedThreadId: number
  selectedTestCaseId?: number
  loadingTests?: boolean
  editingTestcase?: boolean
  runningTests?: boolean
  testCases?: TestCase[]
  testCaseResults?: TestCaseResult[]
  testSuiteRun?: TestSuiteRun
}>()

const emit = defineEmits<{
  (e: 'selectTestCase', testCaseId: number | undefined): void
  (e: 'showTestCaseEditor', show: boolean): void
  (e: 'editingTestcase', editing: boolean): void
  (e: 'deleteTestCase', testCaseThreadId: number): void
  (e: 'runTests'): void
  (e: 'runSingleTest', testCaseId: number): void
  (e: 'newTestCase', testCase: TestCase): void
  (e: 'importAgent' ): void
}>()

const { t } = useI18n()
const { handleError } = useErrorHandler()
const { setCurrentAgent } = useAgentStore()

const api = new ApiService()
const route = useRoute()
const router = useRouter()

const agent = ref<Agent>();
const menu = ref();
const invalidAttrs = ref<string>('')
const backendAgent = ref<Agent>()
const isSaving = ref(false)
const models = ref<LlmModel[]>([])
const toolConfigs = ref<AgentToolConfig[]>([])
const temperatures = [
  { name: t('preciseTemperature'), value: LlmTemperature.PRECISE },
  { name: t('neutralTemperature'), value: LlmTemperature.NEUTRAL },
  { name: t('creativeTemperature'), value: LlmTemperature.CREATIVE }
]
const reasoningEfforts = [
  { name: t('lowEffort'), value: ReasoningEffort.LOW },
  { name: t('mediumEffort'), value: ReasoningEffort.MEDIUM },
  { name: t('highEffort'), value: ReasoningEffort.HIGH }
]
const isGenerating = ref({
  name: false,
  description: false,
  systemPrompt: false
})
const nameMaxLength = 30
const descriptionMaxLength = 100
const showShareConfirmation = ref(false)
const starters = ref<AgentPrompt[]>([])
const { agentsPromptStore, loadAgentPrompts, removePrompt, setPrompts } = useAgentPromptStore()
const publishPrompts = ref(false)
const privatePromptsCount = computed(() => agentsPromptStore.prompts.filter(p => !p.shared).length)
const isLoading = ref(true)
const teams = ref<Team[]>([])
const defaultTeams = ref<Team[]>([new Team(0, t('private')), new Team(1, t('global'))])
const selectedTeam = ref<number | null>(null)
const activeTab = ref<string>('0')
const activeTestCaseMenuId = ref<number | null>(null)
const deletingTestCaseId = ref<number | null>(null)
const renamingTestCaseId = ref<number | null>(null)
const showImportAgent = ref(false)

const loadAgentData = async (agentIdStr: string) => {
  const agentId = parseInt(agentIdStr)
  if (isNaN(agentId)) return

  try {
    agent.value = await api.findAgentById(agentId)
    toolConfigs.value = await api.findAgentToolConfigs(agentId)
    backendAgent.value = { ...agent.value }
    selectedTeam.value = agent.value?.team?.id ?? 0;
    setCurrentAgent(agent.value)
    await loadPromptStarters(agentId)
  } catch (e) {
    handleError(e)
  } finally {
    isLoading.value = false
  }
}

const findSelectedModel = (): LlmModel | undefined => {
  return models.value.find((m) => m.id === agent.value?.modelId)
}

const loadPromptStarters = async (agentId: number) => {
  await loadAgentPrompts(agentId)
  starters.value = agentsPromptStore.prompts.filter(p => p.starter) || []
}

onMounted(async () => {
  try {
    models.value = await api.findModels()
    const user = await loadUserProfile()
    teams.value = [...defaultTeams.value, ...user!.teams.filter(t => !defaultTeams.value.some(dt => dt.id === t.id))];
    if (route.params.agentId) {
      await loadAgentData(route.params.agentId as string)
    }
  }
  finally {
    isLoading.value = false
  }
})


onBeforeRouteUpdate(async (to) => {
  if (to.params.agentId) {
    await loadAgentData(to.params.agentId as string)
  }
})

const onClose = async () => {
  await router.push(`/chat/${props.selectedThreadId}`)
}

const checkAgentFields = () => {
  if (!agent.value) {
    return ''
  }

  const invalidAttrs = []
  if (!agent.value.name && isSelectedPublicTeam.value) {
    invalidAttrs.push(t('shareMissingName'))
  } else if (agent.value.name && agent.value.name.length > nameMaxLength) {
    invalidAttrs.push(t('shareNameTooLong'))
  }

  if (!agent.value.description && isSelectedPublicTeam.value) {
    invalidAttrs.push(t('shareMissingDescription'))
  } else if (agent.value.description && agent.value.description.length > descriptionMaxLength) {
    invalidAttrs.push(t('shareDescriptionTooLong'))
  }


  if (invalidAttrs.length == 0)
    return ''

  const lastVal = invalidAttrs.pop()
  return invalidAttrs.join(', ') + (invalidAttrs.length > 0 ? ' ' + t('shareMissingAnd') + ' ' : '') + lastVal
}

const findTeam = (teamId: number) => {
  return teams.value.find(t => t.id === teamId)
}

const compareAgents = (a: Agent, b: Agent) => {
  return JSON.stringify({ ...a, team: findTeam(a.team?.id || 0) }) === JSON.stringify({ ...b, team: findTeam(b.team?.id || 0) })
}

const updateAgent = async () => {
  if (!agent.value)
    return

  invalidAttrs.value = checkAgentFields()
  if (invalidAttrs.value) {
    return
  }

  if (!agent.value.name?.trim()) {
    agent.value.name = `Agent #${agent.value.id}`
  }

  if (!compareAgents({ ...agent.value, team: findTeam(selectedTeam.value!) }, backendAgent.value!)) {
    isSaving.value = true
    try {
      await api.updateAgent({ ...agent.value!, publishPrompts: publishPrompts.value, teamId: selectedTeam.value || null })
      const updatedAgent = { ...agent.value!, team: findTeam(selectedTeam.value!) }
      agent.value = updatedAgent;
      setCurrentAgent(updatedAgent);
      backendAgent.value = { ...updatedAgent } as Agent
      if (publishPrompts.value) {
        await setPrompts(agentsPromptStore.prompts.map(p => ({ ...p, shared: true })))
      }
      setTimeout(() => {
        isSaving.value = false
      }, 2000)
    } catch (e) {
      handleError(e)
      isSaving.value = false
    }
  }
}

const onChangeTeam = async (team: number | null) => {
  if (team !== agent.value?.team?.id) {
    publishPrompts.value = false
    invalidAttrs.value = checkAgentFields();
    showShareConfirmation.value = true;
  }
}

const onConfirmChangeTeam = async () => {
  await updateAgent()
  showShareConfirmation.value = false
}

const onCancelChangeTeam = async () => {
  selectedTeam.value = agent.value?.team?.id ?? 0;
  showShareConfirmation.value = false
}

const generateAgentField = async (field: AutomaticAgentField, callback: (v: string) => void, generatingCallback: (v: boolean) => void) => {
  try {
    generatingCallback(true)
    const response = await api.generateAgentField(agent.value!.id, field)
    callback(response)
    await updateAgent()
  } catch (e) {
    handleError(e)
  } finally {
    generatingCallback(false)
  }
}

const generateName = async () => {
  await generateAgentField(AutomaticAgentField.NAME, (v) => agent.value!.name = v, (v) => isGenerating.value.name = v)
}

const generateDescription = async () => {
  await generateAgentField(AutomaticAgentField.DESCRIPTION, (v) => agent.value!.description = v, (v) => isGenerating.value.description = v)
}

const generateSystemPrompt = async () => {
  await generateAgentField(AutomaticAgentField.SYSTEM_PROMPT, (v) => agent.value!.systemPrompt = v, (v) => isGenerating.value.systemPrompt = v)
}

const handleStarterDelete = async (starterId: number) => {
  try {
    await removePrompt(agent.value!.id, starterId)
    await loadPromptStarters(agent.value!.id)
  } catch (e) {
    handleError(e)
  }
}

const handleReloadStarters = async () => {
  try {
    await loadPromptStarters(agent.value!.id)
  } catch (e) {
    handleError(e)
  }
}

const onUpdateToolConfigs = async () => {
  toolConfigs.value = await api.findAgentToolConfigs(agent.value!.id)
}

const selectTestCase = (testCaseId: number) => {
  emit('selectTestCase', testCaseId)
}

const onEditTests = () => {
  if (!props.testCases?.length && props.editingTestcase) {
    return
  }
  emit('editingTestcase', !props.editingTestcase)
}

const toggleTestCaseMenu = (testCaseId: number) => {
  activeTestCaseMenuId.value = activeTestCaseMenuId.value === testCaseId ? null : testCaseId
}

const closeTestCaseMenu = () => {
  activeTestCaseMenuId.value = null
}

const onDeleteTestCase = (testCase: TestCase) => {
  deletingTestCaseId.value = testCase.thread.id
  closeTestCaseMenu()
}

const onConfirmDeleteTestCase = async () => {
  try {
    await api.deleteTestCase(agent.value!.id, deletingTestCaseId.value!)

    emit('deleteTestCase', deletingTestCaseId.value!)
    deletingTestCaseId.value = null
  } catch (error) {
    handleError(error)
  }
}

const onRenameTestCase = (testCase: TestCase) => {
  renamingTestCaseId.value = testCase.thread.id
  closeTestCaseMenu()
}

const onSaveTestCaseName = async (newName: string) => {
  try {
    const testCase = props.testCases?.find(tc => tc.thread.id === renamingTestCaseId.value)
    const updatedTestCase = await api.updateTestCase(agent.value!.id, renamingTestCaseId.value!, newName)
    testCase!.thread.name = updatedTestCase.thread.name
    renamingTestCaseId.value = null
  } catch (error) {
    handleError(error)
  }
}

const onCancelRenameTestCase = () => {
  renamingTestCaseId.value = null
}

const onCancelDeleteTestCase = () => {
  deletingTestCaseId.value = null
}

const findTestCaseResult = (testCaseId: number) => {
  return props.testCaseResults?.find((result) => result.testCaseId === testCaseId)
}

watch(activeTab, (newVal) => {
  emit('showTestCaseEditor', newVal === '1')
})

const modelType = computed(() => findSelectedModel()?.modelType)
const isSelectedPublicTeam = computed(() => selectedTeam.value != null && selectedTeam.value > 0)

const shareDialogTranslationKey = computed(() => {
  if (invalidAttrs.value) {
    return isSelectedPublicTeam.value ? 'shareInvalidAttrs' : 'unshareInvalidAttrs'
  }

  if (isSelectedPublicTeam.value) {
    if (agent.value?.team?.id) {
      return 'changeTeamConfirmationMessage'
    }
    return selectedTeam.value === 1 ? 'shareConfirmationMessageGlobal' : 'shareConfirmationMessageTeam'
  }

  return 'unshareConfirmationMessage'
})

const shareDialogTranslationParams = computed(() => ({
  invalidAttrs: invalidAttrs.value,
  team: findTeam(selectedTeam.value!)?.name
}))

const onNewTestCase = async () => {
  try {
    const testCase = await api.addTestCase(agent.value!.id)
    emit('newTestCase', testCase)
  } catch (e) {
    handleError(e)
  }
}

const countResultWithStatus = (status: TestCaseResultStatus) => {
  return props.testCaseResults?.filter((result) => result.status === status).length || 0
}

const exportAgent = async () => {
  try {
    const response = await api.exportAgent(agent.value!.id)
    const url = window.URL.createObjectURL(response)
    const link = document.createElement('a')
    link.href = url
    link.download = response.name
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    handleError(error)
  }
}

const onImportAgent = async (file: UploadedFile) => {
  try {
    showImportAgent.value = false
    await api.importAgent(agent.value!.id, file.file!)
    await loadAgentData(String(agent.value!.id))
    emit('importAgent')
  } catch (error) {
    handleError(error)
  }
}

// Flattens grouped models: showVendor is true only for the first model of each vendor to render logos once per group.
const flatOptions = computed(() => {
  const models = groupedModelsByVendor();
  return models.flatMap((vendorModels) => vendorModels.map((m, i) => ({ ...m, vendor: m.modelVendor, showVendor: i === 0 })));
});

const groupedModelsByVendor = () => {
  const map = new Map<LlmModelVendor, LlmModel[]>();

  for (const model of models.value) {
    if (!map.has(model.modelVendor)) {
      map.set(model.modelVendor, []);
    }
    map.get(model.modelVendor)!.push(model);
  }

  return Array.from(map.values());
}

const vendorLogos: Record<LlmModelVendor, string | undefined> = {
  [LlmModelVendor.OPENAI]: openAiIcon,
  [LlmModelVendor.GOOGLE]: googleIcon,
  [LlmModelVendor.ANTHROPIC]: anthropicIcon
}

</script>

<template>
  <Tabs v-model:value="activeTab" class="h-full flex flex-col">
    <FlexCard header-height="auto" header-class="!py-0" class="flex flex-col h-full">
      <template #header>
        <div class="flex flex-row justify-between items-center">
          <div class="flex flex-row items-center gap-3 mt-1">
            <SimpleButton @click="onClose">
              <IconArrowLeft />
            </SimpleButton>
            <TabList class="!p-0 !pt-3">
              <Tab value="0">
                <div class="flex gap-2">
                  <IconPencil size="20" />
                  {{ t('editAgentTabTitle') }}
                </div>
              </Tab>
              <Tab value="1">
                <div class="flex gap-2">
                  <IconPlayerPlay size="20" />
                  {{ t('testsTabTitle') }}
                </div>
              </Tab>
            </TabList>
            <div v-if="isSaving" class="flex flex-row px-2 items-center text-sm animate-pulse">
              <IconDeviceFloppy />
              <span class="mt-1 ml-1">{{ t('saving') }}</span>
            </div>
          </div>
          <AgentChatMenu
            v-if="activeTab === '0'"
            ref="menu"
            @menu-toggle="(event: Event) => menu?.toggle(event)"
            :items="[
              {
                label: t('exportAgent'),
                tablerIcon: IconDownload,
                command: () => exportAgent()
              }, {
                label: t('importAgent'),
                tablerIcon: IconUpload,
                command: () => showImportAgent = true
              }]"/>
        </div>
      </template>
      <TabPanels class="flex-1 !p-0.5 overflow-hidden">
        <TabPanel value="0" class="h-full overflow-y-auto">
          <AgentEditorPanelSkeleton v-if="isLoading" />
          <div class="flex flex-col gap-3 px-4 py-2 mb-4" v-if="agent && !isLoading">
            <div class="flex flex-row justify-between">
              <div class="form-field">
                <AgentIconEditor v-model:icon="agent.icon" v-model:bg-color="agent.iconBgColor" @change="updateAgent" />
              </div>
              <div class="form-field !flex-row gap-3 items-center">
                <label for="visibility">{{ t('visibilityLabel') }}</label>
                <UserTeamsSelect id="visibility" v-model="selectedTeam" :default-teams="defaultTeams" :default-selected-team="selectedTeam"
                  @change="onChangeTeam" />
              </div>
            </div>
            <div class="form-field relative">
              <label for="name">{{ t('nameLabel') }}</label>
              <InteractiveInput id="name" v-model="agent.name" :maxlength="nameMaxLength"
                :required="isSelectedPublicTeam" @blur="updateAgent" :placeholder="t('namePlaceholder')"
                @end-icon-click="generateName" end-icon="IconWand" :loading="isGenerating.name" />
            </div>
            <div class="form-field relative">
              <label for="description">{{ t('descriptionLabel') }}</label>
              <InteractiveInput id="description" v-model="agent.description" :maxlength="descriptionMaxLength"
                :required="isSelectedPublicTeam" @blur="updateAgent" :placeholder="t('descriptionPlaceholder')"
                @end-icon-click="generateDescription" end-icon="IconWand" :loading="isGenerating.description" />
            </div>
            <div class="flex flex-row gap-3" id="agent-model-container">
              <div class="form-field w-full">
                <label for="model">{{ t('modelLabel') }}</label>
                <Select
                  id="model"
                  v-model="agent.modelId"
                  option-label="name"
                  option-value="id"
                  class="w-full"
                  appendTo="#agent-model-container"
                  overlay-class="left-8! mt-[-20px]! w-[calc(100%-64px)]! p-2! pr-0! h-full! max-h-[45%]!"
                  :options="flatOptions"
                  @change="updateAgent"
                >
                  <template #option="slotProps">
                    <div class="flex items-stretch gap-3 w-full">
                      <div class="w-32 flex items-center self-stretch">
                        <img v-if="slotProps.option.showVendor && slotProps.option.vendor && vendorLogos[slotProps.option.vendor as LlmModelVendor]"
                          :src="vendorLogos[slotProps.option.vendor as LlmModelVendor]"
                          :alt="slotProps.option.vendor"
                           />
                      </div>
                      <div :class="['flex-1 flex flex-col gap-1 hover:bg-pale rounded-md p-3', slotProps.selected ? 'selected-option' : '']">
                        <div class="font-medium">{{ slotProps.option.name }}</div>
                        <div class="text-sm font-normal break-words whitespace-normal">{{ slotProps.option.description }}</div>
                      </div>
                    </div>
                  </template>
                  <template #dropdownicon>
                    <IconCaretRightFilled />
                  </template>
                </Select>
              </div>
              <div class="form-field" v-if="modelType === LlmModelType.CHAT">
                <label for="temperature">{{ t('temperatureLabel') }}</label>
                <SelectButton id="temperature" v-model="agent.temperature" :options="temperatures" option-label="name"
                  option-value="value" :allow-empty="false" @change="updateAgent" />
              </div>
              <div class="form-field" v-if="modelType === LlmModelType.REASONING">
                <label for="reasoningEffort">{{ t('reasoningEffortLabel') }}</label>
                <SelectButton id="reasoningEffort" v-model="agent.reasoningEffort" :options="reasoningEfforts"
                  option-label="name" option-value="value" :allow-empty="false" @change="updateAgent" />
              </div>
            </div>
            <div class="form-field relative">
              <label for="systemPrompt">{{ t('systemPromptLabel') }}</label>
              <InteractiveInput id="systemPrompt" v-model="agent.systemPrompt" @blur="updateAgent" :rows="10"
                :placeholder="t('systemPromptPlaceholder')" end-icon="IconWand" :loading="isGenerating.systemPrompt"
                @end-icon-click="generateSystemPrompt" />
            </div>
            <div class="form-field relative">
              <AgentConversationStarters :starters="starters" @delete="handleStarterDelete" :agent="agent"
                @reload="handleReloadStarters" />
            </div>
            <div class="form-field relative">
              <AgentToolConfigsEditor :agent-id="agent.id" :tool-configs="toolConfigs" @update="onUpdateToolConfigs" />
            </div>
          </div>
        </TabPanel>
        <TabPanel value="1" v-if="!loadingTests" class="flex h-full">
          <div class="w-full flex flex-col gap-6 h-full">
            <div class="flex justify-between">
              <div class="flex flex-row items-center gap-2">
                <AgentAvatar v-if="agent" :agent="agent" :desaturated="true" />
                <div>{{ agent?.name }}</div>
              </div>
              <div class="flex flex-row items-center gap-2">
                <SimpleButton v-if="testCases?.length" shape="square" size="small" @click="$emit('runTests')"
                  :disabled="runningTests">
                    <IconPlayerPlay size="20" />
                    {{ t('runTestsButton') }}
                </SimpleButton>
                <SimpleButton v-if="testCases?.length" :variant="editingTestcase ? 'primary' : undefined" shape="square" size="small"
                  @click="onEditTests" :disabled="runningTests">
                  <div class="flex flex-row items-center gap-1">
                    <IconPencil size="20" />
                    {{ t('editTestsButton') }}
                  </div>
                </SimpleButton>
              </div>
            </div>
            <div v-if="!testCases?.length" class="flex flex-col gap-2">
              <span class="font-bold">{{ t('noTestCasesTitle') }}</span>
              <span class="">{{ t('noTestCasesDescription') }}</span>
            </div>
            <div v-else class="flex flex-col gap-2 min-h-0">
              <div v-if="editingTestcase" class="flex justify-end items-center h-[50px]">
                <SimpleButton shape="square" size="small" @click="onNewTestCase">
                  <IconPlus size="20" />
                  {{ t('newTestCaseButton') }}
                </SimpleButton>
              </div>
              <div class="flex flex-col gap-2 overflow-y-auto ">
                <div v-if="testCaseResults?.length" class="flex items-center justify-between border-1 border-auxiliar-gray rounded-xl px-3 py-2 shadow-xs group h-[50px]">
                  <div>
                    <span v-if="testSuiteRun?.status == TestSuiteRunStatus.RUNNING">{{ t('running') }}</span>
                    <span v-else>{{ t('lastExecution') }}: <span class="font-semibold">{{ moment(testSuiteRun?.executedAt).format('D MMM YYYY HH:mm') }}</span></span>
                  </div>
                  <div class="flex flex-row items-center gap-4">
                    <div class="flex flex-row items-center gap-2" v-tooltip.bottom="t('success')">
                      <IconSquareCheckFilled class="text-success" />
                      <span>{{ countResultWithStatus(TestCaseResultStatus.SUCCESS) }}</span>
                    </div>
                    <div class="flex flex-row items-center gap-2" v-tooltip.bottom="t('failure')">
                      <IconSquareXFilled class="text-error" />
                      <span>{{ countResultWithStatus(TestCaseResultStatus.FAILURE) }}</span>
                    </div>
                    <div class="flex flex-row items-center gap-2" v-tooltip.bottom="t('error')">
                      <IconExclamationMark class="text-white bg-warn rounded-md p-0.5" size="20" />
                      <span>{{ countResultWithStatus(TestCaseResultStatus.ERROR) }}</span>
                    </div>
                    <div class="flex flex-row items-center gap-2" v-tooltip.bottom="t('skipped')">
                      <IconSquareChevronsRightFilled class="text-light-gray" />
                      <span>{{ countResultWithStatus(TestCaseResultStatus.SKIPPED) }}</span>
                    </div>
                  </div>
                </div>

                <div v-for="testCase in (testCases || [])" :key="testCase.thread.id">
                  <Animate v-if="deletingTestCaseId === testCase.thread.id" :effect="AnimationEffect.QUICK_SLIDE_DOWN">
                    <ItemConfirmation class="shadow-none !m-0"
                      :tooltip="t('deleteTestCaseConfirmation', { testCaseName: testCase.thread.name })"
                      @confirm="onConfirmDeleteTestCase" @cancel="onCancelDeleteTestCase" />
                  </Animate>
                  <Animate v-else-if="renamingTestCaseId === testCase.thread.id" :effect="AnimationEffect.QUICK_SLIDE_DOWN"
                    class="w-full">
                    <SidebarEditor :value="testCase.thread.name" :on-save="onSaveTestCaseName"
                      :on-cancel="onCancelRenameTestCase" class="w-full" />
                  </Animate>
                  <div v-else
                    class="border-1 border-auxiliar-gray rounded-xl px-3 py-2 cursor-pointer shadow-xs group h-[50px]"
                    @click="selectTestCase(testCase.thread.id)"
                    :class="{ '!border-abstracta': selectedTestCaseId === testCase.thread.id }">
                    <div class="flex items-center justify-between h-full">
                      <span class="flex-1">{{ testCase.thread.name }}</span>
                      <div class="flex flex-row items-center gap-2">
                        <TestCaseStatus :status="findTestCaseResult(testCase.thread.id)?.status" />
                        <AgentTestcaseMenu :test-case="testCase"
                          :active="activeTestCaseMenuId === testCase.thread.id"
                          @toggle-active="() => toggleTestCaseMenu(testCase.thread.id)"
                          @close-menu="() => closeTestCaseMenu()"
                          :items="editingTestcase ? [
                            {
                              label: t('renameTestCaseTooltip'),
                              tablerIcon: IconPencil,
                              command: () => onRenameTestCase(testCase)
                            },
                            {
                              label: t('deleteTestCaseTooltip'),
                              tablerIcon: IconTrash,
                              command: () => onDeleteTestCase(testCase)
                            }
                          ] : [
                            {
                              label: t('runSingleTestMenuItem'),
                              tablerIcon: IconPlayerPlay,
                              command: () => $emit('runSingleTest', testCase.thread.id),
                              disabled: runningTests
                            }
                          ]" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabPanel>
      </TabPanels>
    </FlexCard>
  </Tabs>

  <Dialog v-model:visible="showShareConfirmation"
    :header="t(isSelectedPublicTeam ? agent?.team?.id ? 'changeTeamConfirmationTitle' : 'shareConfirmationTitle' : 'unshareConfirmationTitle', { oldTeam: agent?.team?.name, newTeam: findTeam(selectedTeam!)?.name })"
    :modal="true" :draggable="false" :resizable="false" :closable="false" class="max-w-200">
    <div class="flex flex-col gap-2">
      <div class="flex flex-row gap-2 items-start whitespace-pre-line">
        <IconAlertTriangleFilled color="var(--color-warn)" v-if="invalidAttrs" />
        {{ t(shareDialogTranslationKey, shareDialogTranslationParams) }}
      </div>
      <div v-if="!invalidAttrs && isSelectedPublicTeam && privatePromptsCount > 0"
        class="flex items-center gap-2 py-4 mt-3 border-t-1 border-auxiliar-gray">
        <div class="flex flex-row gap-2 items-start">
          <ToggleSwitch v-model="publishPrompts" />
          <div class="flex flex-col">
            <label for="publish-prompts"> {{ t('publishPrompts', { count: privatePromptsCount }) }} </label>
            <label class="text-sm text-light-gray">{{ t('publishPromptsDescription') }}</label>
          </div>
        </div>
      </div>
      <div class="flex flex-row gap-2 justify-end">
        <SimpleButton @click="onCancelChangeTeam" shape="square" variant="secondary">{{ t('cancel') }}</SimpleButton>
        <SimpleButton @click="onConfirmChangeTeam" v-if="!invalidAttrs" variant="primary" shape="square">{{ t(
          invalidAttrs ? 'backToEdit' : isSelectedPublicTeam ? agent?.team?.id ? 'changeTeam' : 'publish' : 'unpublish')
        }}</SimpleButton>
      </div>
    </div>
  </Dialog>
  <AgentImportDialog v-model:visible="showImportAgent" @import="onImportAgent" />
</template>

<i18n lang="json">{
  "en": {
    "shareTooltip": "Share",
    "unshareTooltip": "Unshare",
    "editAgentTitle": "Edit {name}",
    "nameLabel": "Name",
    "descriptionLabel": "Description",
    "modelLabel": "Model",
    "systemPromptLabel": "Instructions",
    "saving": "Saving...",
    "namePlaceholder": "Enter a name for the agent",
    "descriptionPlaceholder": "What does this agent do?",
    "systemPromptPlaceholder": "Write the instructions for this agent",
    "public": "Public",
    "private": "Private",
    "shareConfirmationTitle": "Do you want to make this agent public?",
    "shareInvalidAttrs": "To share the agent you need to specify {invalidAttrs}.",
    "unshareInvalidAttrs": "To make this agent private you need to specify {invalidAttrs}.",
    "shareMissingName": "a name",
    "shareNameTooLong": "a shorter name",
    "shareMissingAnd": "and",
    "shareMissingDescription": "a description",
    "shareDescriptionTooLong": "a shorter description",
    "shareConfirmationMessageGlobal": "When you make an agent public it will be visible to everyone in the home page of Tero, so we can all benefit from what you have created.\n\nAdditionally, all future modifications to the agent will be immediately available to the rest of the users.",
    "shareConfirmationMessageTeam": "When you make an agent public it will be visible to everyone in the {team} team, so they can benefit from what you have created.\n\nAdditionally, all future modifications to the agent will be immediately available to the rest of the users.",
    "unshareConfirmationTitle": "Do you want to make this agent private?",
    "unshareConfirmationMessage": "When you make an agent private it will no longer be visible, but the users that have already used it will keep being able to use it.\n\nAdditionally, future modifications to the agent will still be available to these users.",
    "unpublish": "Make private",
    "publish": "Publish",
    "backToEdit": "Back to edit",
    "cancel": "Cancel",
    "publishPrompts": "Do you want to publish your {count} private prompts?",
    "publishPromptsDescription": "If you want to review your prompts go to the chats prompts panel",
    "visibilityLabel": "Who can see it?",
    "global": "Global",
    "changeTeamConfirmationTitle": "Change the team of this agent from {oldTeam} to {newTeam}?",
    "changeTeamConfirmationMessage": "When you change the team of an agent only the users in the new team will be able to use it.",
    "changeTeam": "Change team",
    "temperatureLabel": "Temperature",
    "reasoningEffortLabel": "Reasoning",
    "preciseTemperature": "Precise",
    "neutralTemperature": "Neutral",
    "creativeTemperature": "Creative",
    "lowEffort": "Low",
    "mediumEffort": "Medium",
    "highEffort": "High",
    "editAgentTabTitle": "Edit",
    "testsTabTitle": "Tests",
    "noTestCasesTitle": "You don't have test cases for this agent yet",
    "noTestCasesDescription": "Create your first test case to validate that the agent meets the expected requirements.",
    "editTestsButton": "Edit",
    "runTestsButton": "Run all",
    "runSingleTestMenuItem": "Run",
    "editTestCaseTooltip": "Edit",
    "renameTestCaseTooltip": "Rename",
    "deleteTestCaseTooltip": "Delete",
    "deleteTestCaseConfirmation": "Delete {testCaseName}?",
    "newTestCaseButton": "Add",
    "lastExecution": "Last execution",
    "noTestCasesResults": "No test cases results yet",
    "running": "Running...",
    "exportAgent": "Export",
    "importAgent": "Import",
    "success": "Success",
    "failure": "Failed",
    "error": "Error running",
    "skipped": "Skipped"
  },
  "es": {
    "shareTooltip": "Compartir",
    "unshareTooltip": "Dejar de compartir",
    "editAgentTitle": "Editar {name}",
    "nameLabel": "Nombre",
    "descriptionLabel": "Descripción",
    "modelLabel": "Modelo",
    "systemPromptLabel": "Instrucciones",
    "saving": "Guardando...",
    "namePlaceholder": "Ingresa el nombre del agente",
    "descriptionPlaceholder": "¿Qué hace este agente?",
    "systemPromptPlaceholder": "Escribe las instrucciones de este agente",
    "public": "Público",
    "private": "Privado",
    "shareConfirmationTitle": "¿Quieres hacer este agente público?",
    "shareConfirmationMessageGlobal": "Cuando haces un agente público, este será visible en la página de inicio de Tero para que todos podamos beneficiarnos de lo que has creado.\n\nAdemás, todas las modificaciones futuras al agente estarán disponibles inmediatamente para el resto de sus usuarios.",
    "shareConfirmationMessageTeam": "Cuando haces un agente público, este será visible para los miembros del equipo {team}, para que ellos puedan beneficiarse de lo que has creado.\n\nAdemás, todas las modificaciones futuras al agente estarán disponibles inmediatamente para el resto de sus usuarios.",
    "shareInvalidAttrs": "Para compartir el agente, primero necesitas especificar {invalidAttrs}.",
    "unshareInvalidAttrs": "Para hacer este agente privado, primero necesitas especificar {invalidAttrs}.",
    "shareMissingName": "un nombre",
    "shareNameTooLong": "un nombre más corto",
    "shareMissingAnd": "y",
    "shareMissingDescription": "una descripción",
    "shareDescriptionTooLong": "una descripción más corta",
    "unshareConfirmationTitle": "¿Quieres hacer este agente privado?",
    "unshareConfirmationMessage": "Cuando haces un agente privado ya no será visible, pero los usuarios que ya lo han utilizado seguirán siendo capaces de usarlo.\n\nAdemás, las modificaciones futuras al agente seguirán estando disponibles para estos usuarios.",
    "unpublish": "Hacer privado",
    "publish": "Publicar",
    "backToEdit": "Volver a editar",
    "cancel": "Cancelar",
    "publishPrompts": "¿Quieres publicar tus {count} prompts privados?",
    "publishPromptsDescription": "Si quieres revisar tus prompts ve al panel de prompts en el chat",
    "visibilityLabel": "¿Quién puede verlo?",
    "global": "Global",
    "changeTeamConfirmationTitle": "¿Quieres cambiar el equipo de este agente de {oldTeam} a {newTeam}?",
    "changeTeamConfirmationMessage": "Cuando cambias el equipo de un agente, solo lo podrán usar los usuarios del nuevo equipo.",
    "changeTeam": "Cambiar equipo",
    "temperatureLabel": "Temperatura",
    "reasoningEffortLabel": "Razonamiento",
    "preciseTemperature": "Preciso",
    "neutralTemperature": "Neutro",
    "creativeTemperature": "Creativo",
    "lowEffort": "Bajo",
    "mediumEffort": "Medio",
    "highEffort": "Alto",
    "editAgentTabTitle": "Editar",
    "testsTabTitle": "Tests",
    "noTestCasesTitle": "Aún no tienes test cases para este agente",
    "noTestCasesDescription": "Crea tu primer test case para validar que el agente cumple los requisitos esperados.",
    "editTestsButton": "Editar",
    "runTestsButton": "Ejecutar todos",
    "runSingleTestMenuItem": "Ejecutar",
    "editTestCaseTooltip": "Editar",
    "renameTestCaseTooltip": "Renombrar",
    "deleteTestCaseTooltip": "Eliminar",
    "deleteTestCaseConfirmation": "¿Eliminar {testCaseName}?",
    "newTestCaseButton": "Agregar",
    "lastExecution": "Última ejecución",
    "noTestCasesResults": "No hay resultados de ejecución aún",
    "running": "Ejecutando...",
    "exportAgent": "Exportar",
    "importAgent": "Importar",
    "success": "Pasó",
    "failure": "Falló",
    "error": "Error al ejecutar",
    "skipped": "Omitido"
  }
}</i18n>

<style scoped lang="scss">
@import '@/assets/styles.css';

:deep(.p-inputnumber) .p-inputtext {
  @apply pr-9
}

:deep(.p-inputnumber.loading) .p-inputtext {
  @apply animate-glowing
}

:deep(.p-select-list) {
  gap: 8px !important;
}

:deep(.p-select-option) {
  padding: 0 !important;
}

:deep(.p-select-option.p-select-option-selected) {
  background: transparent !important;
}

:deep(.p-select-option.p-focus) {
  background: transparent !important;
  border-color: transparent !important;
}

.selected-option {
  background-color: #f4f4f4;
}

:deep(.p-select-list-container) {
  max-height: none!important;
  height: 100%!important;
}
</style>
