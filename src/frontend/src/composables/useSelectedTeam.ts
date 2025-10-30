import { ref, computed } from 'vue'

const selectedTeamState = ref<number | null>(null)

export function useSelectedTeam() {
  const selectedTeam = computed(() => selectedTeamState.value)

  const updateSelectedTeam = (teamId: number | null) => {
    selectedTeamState.value = teamId
  }

  return { selectedTeam, updateSelectedTeam }
}
