<script lang="ts" setup>
import { onBeforeMount } from 'vue';
import { useRouter } from 'vue-router';
import auth from '@/services/auth';

const router = useRouter();

onBeforeMount(async () => {
  try {
    await auth.logout();
  } catch (e) {
    console.error('Error during logout, redirecting to landing page', e);
    router.push('/landing');
  }
});
</script>

<template>
  <div></div>
</template>
