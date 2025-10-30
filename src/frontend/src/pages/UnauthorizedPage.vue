<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
const { t } = useI18n()
const router = useRouter()
</script>

<template>
    <ErrorPageLayout :code="403" :title="t('title')" :description="t('description')">
      <template #actions>
        <SimpleButton shape="square" @click="router.push('/')">
          <IconArrowLeft/>
          <span>{{ t('goBack') }}</span>
        </SimpleButton>
      </template>
    </ErrorPageLayout>
</template>

<i18n>
  {
    "en": {
      "title": "Unauthorized",
      "description": "It seems you took a wrong turn. We'll take you back to the right path.",
      "goBack": "Go back"
    },
    "es": {
      "title": "Acceso no autorizado",
      "description": "Parece que tomaste un camino equivocado. Vamos a llevarte de vuelta al buen sendero.",
      "goBack": "Volver"
    }
  }
</i18n>
