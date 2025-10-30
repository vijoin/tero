<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
const { t } = useI18n()
const router = useRouter()
</script>
<template>
  <ErrorPageLayout :code="404" :title="t('title')" :description="t('description')">
    <template #actions>
      <SimpleButton shape="square" @click="router.push('/')">
        <IconArrowLeft/>
        <span>{{ t('backToHome') }}</span>
      </SimpleButton>
      <SimpleButton shape="square" @click="router.push('/discover')">
        <IconApps/>
        <span>{{ t('exploreAgents') }}</span>
      </SimpleButton>
    </template>
  </ErrorPageLayout>
</template>

<i18n>
  {
    "en": {
      "title": "Page not found",
      "description": "Our agents have many skills, but finding broken pages is not one of them. Sorry!",
      "backToHome": "Back to home",
      "exploreAgents": "Explore available agents"
    },
    "es": {
      "title": "Página no encontrada",
      "description": "Nuestros agentes tienen muchas habilidades, pero encontrar páginas rotas no es una de ellas. ¡Lo sentimos!",
      "backToHome": "Regresar al inicio",
      "exploreAgents": "Explorar agentes disponibles"
    }
  }
</i18n>
