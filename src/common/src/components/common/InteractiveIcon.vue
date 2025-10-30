<script setup lang="ts">
import type { Icon } from '@tabler/icons-vue';

const { icon } = defineProps<{
  icon: Icon;
}>();

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void;
}>();
</script>

<template>
  <div
    class="text-light-gray hover:text-abstracta cursor-pointer"
    @click="emit('click', $event)">
    <component :is="icon" />
  </div>
</template>

