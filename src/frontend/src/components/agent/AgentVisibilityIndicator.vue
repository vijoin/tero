<script lang="ts" setup>
defineProps<{
  shared: boolean
}>()
</script>

<template>
  <IconLock v-if="!shared" class="text-light-gray !w-5" />
</template>
