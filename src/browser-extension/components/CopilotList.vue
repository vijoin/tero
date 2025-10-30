<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'
import { IconCirclePlus, IconRefresh, IconTrashX, IconLoader } from '@tabler/icons-vue'
import { findAllAgents, removeAgent, removeAllAgents, updateAgents } from '~/utils/agent-repository'
import { Agent, AgentType, AgentSource } from '~/utils/agent'

defineEmits<{
  (e: 'close'): void
  (e: 'activateAgent', agentId: string): void
}>();
const { t } = useI18n()
const toast = useToast()
const agents = ref<Agent[]>()
const showAddCopilot = ref(false)
const deletingIndex = ref(-1)
const isLoading = ref(false)

onBeforeMount(async () => {
  agents.value = await findAllAgents()

  // this logic avoid initial empty list of agents in development environment due to asynchronous loading of agents 
  // and this component being mounted before agents are loaded
  if (agents.value?.length === 0 && import.meta.env.DEV) {
    loadDevAgents()
  }
});

const loadDevAgents = () => {
  const startTime = Date.now()
  const timeoutMillis = 30000
  const pollInterval = setInterval(async () => {
    try {
      agents.value = await findAllAgents()
      if (agents.value.length > 0 || (Date.now() - startTime) >= timeoutMillis) {
        clearInterval(pollInterval)
      }
    } catch (e) {
      console.error('Error loading agents', e)
      clearInterval(pollInterval)
    }
  }, 500)
}

const removeCopilot = (index: number) => {
  deletingIndex.value = index
};

const closeDeletionConfirmation = () => {
  deletingIndex.value = -1
};

const confirmRemoval = async () => {
  let agent = agents.value![deletingIndex.value]
  await removeAgent(agent.manifest.id!)
  await agent.tearDown()
  agents.value!.splice(deletingIndex.value, 1)
  closeDeletionConfirmation()
};

const onCopilotAdded = (agent: Agent) => {
  agents.value!.push(agent)
  showAddCopilot.value = false
};

const refreshAgents = async () => {
  isLoading.value = true
  let existingAgents: Agent[] = []
  try {
    existingAgents = await findAllAgents()
    const agentUrls = [...new Set(existingAgents.map(agent => agent.url))] 
    await removeAllAgents()
    await Promise.all(agentUrls.map(url => AgentSource.loadAgentsFromUrl(url)))
    agents.value = await findAllAgents()
  } catch (e: any) {
    agents.value = existingAgents
    // Restore existing agents as backup in case removeAllAgents() was called but subsequent operations failed
    await updateAgents(existingAgents)
    toast.error(t('refreshError'))
  } finally {
    isLoading.value = false
  }
};
</script>

<template>
  <PageOverlay>
    <template v-slot:headerActions>
      <button v-if="agents && agents.length > 0" @click="refreshAgents" :title="t('refreshTitle')">
        <IconRefresh class="w-6.5 h-6.5 relative" />
      </button>
      <BtnClose @click="$emit('close')" />
    </template>
    <template v-slot:content>
      <div v-if="isLoading" class="flex justify-center items-center w-full h-full">
        <IconLoader class="animate-spin text-violet-600" />
      </div>
      <div v-if="!isLoading" class="flex flex-row py-3">
        <div class="flex items-center text-base cursor-pointer" @click="showAddCopilot = true"><IconCirclePlus />{{ t('addTitle') }}</div>
      </div>
      <div v-if="!isLoading" v-for="(agent, index) in agents" :key="agent.manifest.id" class="flex flex-row py-3 ">
        <div class="flex flex-row flex-auto self-center items-center cursor-pointer gap-2" @click="$emit('activateAgent', agent.manifest.id)">
          <div class="w-7 h-7 flex flex-row items-center rounded-full overflow-hidden">
            <img :src="agent.logo" class="w-full h-full object-contain m-0" />
          </div>
          <div class="text-lg font-medium">
            {{ agent.manifest.name! }}
          </div>
        </div>
        <button v-if="agent.type !== AgentType.TeroAgent" @click="removeCopilot(index)">
          <IconTrashX class="action-icon" />
        </button>
      </div>
    </template>
    <template v-slot:modalsContainer>
      <ModalForm :title="t('removeTitle')" :show="deletingIndex >= 0" @close="closeDeletionConfirmation" @save="confirmRemoval" :button-text="t('removeButton')">
        {{
          t('removeConfirmation', {
            agentName: agents ? agents[deletingIndex].manifest.name : ''
          })
        }}
      </ModalForm>
      <AddCopilotModal :show="showAddCopilot" @close="showAddCopilot = false" @saved="onCopilotAdded" />
    </template>
  </PageOverlay>
</template>

<i18n lang="json">
{
  "en": {
    "addTitle": "Add copilot",
    "removeTitle": "Remove copilot",
    "removeButton": "Remove",
    "removeConfirmation": "Are you sure you want to remove the copilot {agentName}?",
    "refreshTitle": "Refresh agents",
    "refreshError": "Could not refresh agents. Try again and if the problem persists contact support."
  },
  "es" : {
    "addTitle": "Agregar copiloto",
    "removeTitle": "Quitar copiloto",
    "removeButton": "Quitar",
    "removeConfirmation": "¿Estás seguro de borrar el copiloto {agentName}?",
    "refreshTitle": "Actualizar copilotos",
    "refreshError": "No se pudieron actualizar los copilotos. Intenta de nuevo y si el problema persiste contacta a soporte."
  }
}
</i18n>
