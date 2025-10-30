<script lang="ts" setup>
import { useDateRange } from '@/composables/useDateRange'
import { ref } from 'vue'
import { MY_TEAM_ID } from '@/services/api'
import { AnimationEffect } from '@tero/common/utils/animations.js'
import { useSelectedTeam } from '@/composables/useSelectedTeam'

const { fromDate, toDate } = useDateRange()
const { selectedTeam, updateSelectedTeam } = useSelectedTeam()
const dashboardUpdateKey = ref(0)

const handleUpdateUsers = () => {
  dashboardUpdateKey.value++
}

const handleSelectedTeamChanged = async (teamId: number) => {
  updateSelectedTeam(teamId)
}
</script>

<template>
  <div class="flex h-full w-full gap-4 min-h-0 flex-1 translate-y-1">
    <Animate :effect="AnimationEffect.SLIDE_IN_RIGHT" class="!w-full h-full" v-if="selectedTeam != null && selectedTeam != MY_TEAM_ID">
      <DashboardCardUsers :from-date="fromDate" :to-date="toDate" :team-id="selectedTeam" @update-users="handleUpdateUsers" @selected-team-changed="handleSelectedTeamChanged" />
    </Animate>
  </div>
</template>
