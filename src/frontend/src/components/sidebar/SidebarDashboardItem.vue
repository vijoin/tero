<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

const router = useRouter();
const { t } = useI18n();

const navigateToDashboard = () => {
  router.push('/console')
}
</script>

<template>
  <SidebarButton :title="t('dashboardButtonTitle')" icon="IconDeviceDesktopAnalytics" @click="navigateToDashboard" />
</template>

<i18n>
{
    "en": {
        "dashboardButtonTitle": "AI Console"
    },
    "es": {
        "dashboardButtonTitle": "Consola IA"
    }
}
</i18n>