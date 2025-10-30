<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { Agent, LlmModelType } from '@/services/api';

const { t } = useI18n();

const { agent, modelType } = defineProps<{
  agent: Agent;
  modelType: LlmModelType;
}>();

</script>

<template>
    {{ LlmModelType.CHAT === modelType ? t(`${agent.temperature!.toLowerCase()}Temperature`) : t(`${agent.reasoningEffort!.toLowerCase()}Effort`) }}
</template>

<i18n>
  {
    "en": {
      "preciseTemperature": "Precise",
      "neutralTemperature": "Neutral",
      "creativeTemperature": "Creative",
      "lowEffort": "Low",
      "mediumEffort": "Medium",
      "highEffort": "High",
    },
    "es": {
      "preciseTemperature": "Preciso",
      "neutralTemperature": "Neutral",
      "creativeTemperature": "Creativo",
      "lowEffort": "Bajo",
      "mediumEffort": "Medio",
      "highEffort": "Alto",
    }
  }
</i18n>