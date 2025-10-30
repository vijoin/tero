<script lang="ts" setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n();
const searchQuery = ref('');

const props = defineProps<{
  isSearching: boolean
}>();

const emit = defineEmits<{
  (e: 'search', query: string): void
  (e: 'invitationAccepted'): void
}>();

watch(searchQuery, (newQuery) => {
  emit('search', newQuery);
});

const handleInvitationAccepted = () => {
  emit('invitationAccepted');
};

</script>

<template>
  <RightPanelHeader @invitation-accepted="handleInvitationAccepted" :invitation-accepted="true" >
    <template #center>
      <div class="flex justify-center items-center h-full w-full">
        <div class="w-full max-w-md relative">
          <InteractiveInput
            v-model="searchQuery"
            variant="light"
            :placeholder="t('findPerfectAgent')"
            :start-icon="props.isSearching ? 'IconLoader' : 'IconSearch'"
            :loading="props.isSearching"
            />
        </div>
      </div>
    </template>
  </RightPanelHeader>
</template>

<i18n>
{
  "en": {
    "findPerfectAgent": "Find the perfect agent for you"
  },
  "es": {
    "findPerfectAgent": "Encuentra el agente perfecto para ti"
  }
}
</i18n> 