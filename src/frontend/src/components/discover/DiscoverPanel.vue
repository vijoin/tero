<script lang="ts" setup>
import { ref } from 'vue'
import FlexCard from '@tero/common/components/common/FlexCard.vue';
import DiscoverHeader from '@/components/discover/DiscoverHeader.vue';
import DiscoverTabs from '@/components/discover/DiscoverTabs.vue';

const searchQuery = ref('');
const isSearching = ref(false);
const discoverTabsRef = ref();

const handleSearch = (query: string) => {
  searchQuery.value = query;
}

const handleInvitationAccepted = () => {
  if (discoverTabsRef.value) {
    discoverTabsRef.value.refreshTabs();
  }
}
</script>

<template>
  <FlexCard>
    <template #header>
      <DiscoverHeader
        @search="handleSearch"
        @invitation-accepted="handleInvitationAccepted"
        :isSearching="isSearching"
      />
    </template>
    <div class="flex flex-col h-full w-full relative overflow-hidden">
      <DiscoverTabs
        ref="discoverTabsRef"
        :search-query="searchQuery"
        :isSearching="isSearching"
        @searching="isSearching = $event"
      />
    </div>
  </FlexCard>
</template>
