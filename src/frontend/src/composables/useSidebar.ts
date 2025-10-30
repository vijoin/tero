import { ref } from 'vue';

const isSidebarCollapsed = ref(false);

export function useSidebar() {
  const toggleSidebar = () => {
    isSidebarCollapsed.value = !isSidebarCollapsed.value;
  };
  return {
    isSidebarCollapsed,
    toggleSidebar,
  };
} 