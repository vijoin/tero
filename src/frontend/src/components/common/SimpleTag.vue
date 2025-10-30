<script setup lang="ts">
  defineProps<{
    text: string;
  }>();
</script>
<template>
  <span class="block bg-dark-gray text-white text-xs px-2 py-1 rounded-full font-semibold max-w-50 truncate w-fit">
    {{ text }}
  </span>
</template>
