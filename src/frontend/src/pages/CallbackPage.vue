<script lang="ts" setup>
import { onBeforeMount } from 'vue';
import auth from '@/services/auth';

onBeforeMount(async () => {
  await auth.loginCallback();

  window.location.href = `/`;
});
</script>

<template>
  <div></div>
</template>
