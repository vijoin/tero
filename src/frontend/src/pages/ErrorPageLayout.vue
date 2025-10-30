<script setup lang="ts">
const props = defineProps<{code: Number, title: String, description: String}>()
</script>

<template>
  <div class="h-full w-full flex flex-col items-center justify-center text-center p-4 translate-y-[-5%]">
    <div class="text-[280px] font-medium mb-[-50px]">{{ props.code }}</div>
    <h1 class="text-2xl font-medium mb-2">
      {{ props.title }}
    </h1>
    <p class="font-light mb-8 max-w-lg mx-auto">
      {{ props.description }}
    </p>
    <div class="flex gap-4 justify-center">
      <slot name="actions" />
    </div>
  </div>
</template>
