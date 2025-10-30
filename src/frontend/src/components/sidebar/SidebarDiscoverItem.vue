<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

const router = useRouter();
const { t } = useI18n();

const navigateToDiscover = () => {
  router.push('/discover');
}

</script>

<template>
  <SidebarButton :title="t('discoverButtonTitle')" icon="IconApps" @click="navigateToDiscover" />
</template>

<i18n>
{
    "en": {
        "discoverButtonTitle": "Explore agents"
    },
    "es": {
        "discoverButtonTitle": "Explorar agentes"
    }
}
</i18n>