<script setup lang="ts">
import type { MenuItem } from 'primevue/menuitem';

defineProps<{
    item: MenuItem;
}>();
</script>

<template>
    <div class="flex items-center gap-2 px-2 py-1 cursor-pointer">
        <component :is="item.tablerIcon" size="20" class="aligned-menu-item-icon"/>
        <span>{{ item.label }}</span>
    </div>
</template>

<style>
/* Align the icon with the text */
.aligned-menu-item-icon {
    position: relative;
    bottom: 1px;
}
</style>