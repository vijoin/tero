<script setup lang="ts">
import type { Thread } from '@/services/api';
import { onMounted, ref } from 'vue';
import { useRoute, onBeforeRouteUpdate, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const threadId = ref<number>();

const handleSelectChat = (chat:Thread)=>{
  router.push(`/chat/${chat.id}`);
}

onMounted(async () => {
  threadId.value = parseInt(route.params.threadId as string);
});

onBeforeRouteUpdate(async (to) => {
  threadId.value = parseInt(to.params.threadId as string);
});

</script>

<template>
  <ChatPanel v-if="threadId" :threadId="threadId" @select-chat="handleSelectChat"/>
</template>
