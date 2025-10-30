<script setup lang="ts">
import { useSidebar } from '@/composables/useSidebar';

const { isSidebarCollapsed } = useSidebar();

defineProps<{
  title: string,
  icon: string,
  onClick: () => void
}>()

</script>

<template>
<div class="flex items-center gap-2 justify-between" @click="onClick">
    <SidebarItem variant="primary" class="group w-full" :class="isSidebarCollapsed ? 'justify-center' : ''">
      <div class="flex items-center" :class="isSidebarCollapsed ? 'justify-center w-full' : 'gap-2'">
        <div class="flex-shrink-0 flex items-center">
          <Avatar class="!bg-transparent" shape="circle">
          <template #icon>
              <component :is="icon" stroke-width="2" class="group-hover:text-white" />
          </template>
          </Avatar>
        </div>
        <span v-if="!isSidebarCollapsed" class="line-clamp-1 min-w-0 flex-1 font-medium">{{ title }}</span>
      </div>
    </SidebarItem>
  </div>
</template>

