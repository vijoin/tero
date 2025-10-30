<script lang="ts" setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Agent } from '~/utils/agent'
import { ExistingAgentError } from '~/utils/agent-repository'
import { ValidationResult } from '~/utils/validation';
import { AgentSource } from '~/utils/agent'

defineProps<{ show: boolean }>()
const emit = defineEmits<{
  (e: 'close'): void,
  (e: 'saved', prompt: Agent): void
}>()
const { t } = useI18n()
const url = ref('')
const validation = ref(ValidationResult.valid())

const save = async () => {
  const urlValue = parseUrl(url.value)
  try {
    const agents = await AgentSource.loadAgentsFromUrl(urlValue)
    for (const agent of agents) {
      emit('saved', agent)
    }
  } catch (e: any) {
    console.error(`There was a problem adding agent from ${url.value}`, e)
    validation.value = ValidationResult.error(t(e instanceof ExistingAgentError ? 'existingAgentError' : 'agentAddError'))
  }
}

const parseUrl = (urlToParse: string): string => {
  const newUrl = urlToParse.endsWith("/") ? urlToParse.slice(0, -1) : urlToParse;
  const manifestPath = "/manifest.json";
  return newUrl.endsWith(manifestPath) ? newUrl.slice(0, -manifestPath.length) : newUrl;
}

watch(url, () => {
  validation.value = ValidationResult.valid()
})

</script>

<template>
  <ModalForm :title="t('title')" :button-text="t('saveButton')" :show="show" @close="$emit('close')" @save="save">
    <FormInput label="URL" v-model="url" focused :validationProp="validation" />
  </ModalForm>
</template>

<i18n>
{
  "en": {
    "title": "Add Copilot",
    "saveButton": "Add",
    "existingAgentError": "You have already added a copilot with same ID. You should remove it or verify if your new copilot needs to change its ID in manifest.json",
    "agentAddError": "Could not add the copilot. Verify that you can get the manifest.json from the provided URL and that it has proper format"
  },
  "es": {
    "title": "Agregar Copiloto",
    "saveButton": "Agregar",
    "existingAgentError": "Ya agregaste un copiloto con el mismo identificador. Deberías quitar el existente o verificar si tu nuevo copiloto necesita cambiar su identificador en el manifest.json",
    "agentAddError": "No se pudo agregar el copiloto. Verifica que puedes obtener el manifest.json desde la URL provista y que el formato del mismo es el correcto"
  }
}
</i18n>
