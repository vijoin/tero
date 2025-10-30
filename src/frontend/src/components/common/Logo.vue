<script setup lang="ts">
import logo from '@/assets/images/logo.webp'

const { width = 'auto', height = '56px' } = defineProps<{
    width?: string,
    height?: string
}>();
</script>

<template>
  <img :src="logo" alt="Logo" :style="{ width: width, height: height }" class="object-contain hidden md:block"/>
</template>
