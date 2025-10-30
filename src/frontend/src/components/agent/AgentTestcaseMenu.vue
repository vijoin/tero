<script setup lang="ts">
import { ref } from 'vue';
import type { MenuItem } from 'primevue/menuitem';
import type { TestCase } from '@/services/api';
import SimpleButton from '../../../../common/src/components/common/SimpleButton.vue';
import MenuItemTemplate from '../../../../common/src/components/common/MenuItemTemplate.vue';

withDefaults(defineProps<{
  testCase?: TestCase;
  items?: MenuItem[];
  active?: boolean;
}>(), {
  active: false
});

const menu = ref();
const isMenuOpen = ref(false);

const emit = defineEmits<{
  (e: 'toggleActive'): void;
  (e: 'closeMenu'): void;
}>();

const toggle = (event: Event) => {
  menu.value?.toggle(event);
  emit('toggleActive');
};

const closeMenu = () => {
  emit('closeMenu');
}

defineExpose({
  menu,
  isMenuOpen,
  toggle
});
</script>

<template>
  <div v-click-outside="closeMenu">
    <SimpleButton
      class="rounded-lg"
      variant="muted"
      size="small"
      @click.stop.prevent="toggle">
      <IconDots stroke-width="2" :class="!active ? 'text-light-gray' : 'text-abstracta'" />
    </SimpleButton>

    <Menu
      ref="menu"
      :model="items ?? []"
      :popup="true"
      @show="isMenuOpen = true"
      @hide="isMenuOpen = false"
      @keydown.esc="closeMenu">
      <template #item="{ item }">
        <MenuItemTemplate :item="item"/>
      </template>
    </Menu>
  </div>
</template>
