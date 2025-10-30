<script lang="ts" setup>
import { onBeforeMount } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';

const route = useRoute();
const { t } = useI18n();

onBeforeMount(() => {
  const { code, state } = route.query;
  window.opener.postMessage({
      type: 'oauth_callback',
      toolId: route.params.toolId,
      code: code,
      state: state,
    }, window.location.origin);
});
</script>

<template>
  <div class="flex items-center justify-center h-screen">
    <p>{{ t('processingAuthentication') }}</p>
  </div>
</template>

<i18n>
  {
    "en": {
      "processingAuthentication": "Processing authentication..."
    },
    "es": {
      "processingAuthentication": "Procesando autenticación..."
    }
  }
</i18n>