<script lang="ts" setup>
import { AnimationEffect } from '@tero/common/utils/animations.js'
import { MY_TEAM_ID } from '@/services/api'
import { useSelectedTeam } from '@/composables/useSelectedTeam'
import { useDateRange } from '@/composables/useDateRange'

const { fromDate, toDate } = useDateRange()
const { selectedTeam } = useSelectedTeam()

</script>

<template>
  <div class="h-full flex flex-col gap-4">
    <div class="flex w-full">
      <DashboardImpactSummaryCards v-if="selectedTeam != null" :from-date="fromDate" :to-date="toDate" :team-id="selectedTeam" />
    </div>
    <div class="flex h-full w-full gap-4 min-h-0 flex-1 translate-y-1">
      <Animate :effect="AnimationEffect.SLIDE_IN_LEFT" class="h-full" :class="selectedTeam == MY_TEAM_ID ? '!w-full' : '!w-1/2'">
        <DashboardImpactCardTopAgents v-if="selectedTeam != null" :from-date="fromDate" :to-date="toDate" :team-id="selectedTeam" />
      </Animate>
      <Animate :effect="AnimationEffect.SLIDE_IN_RIGHT" class="!w-1/2" v-if="selectedTeam != null && selectedTeam != MY_TEAM_ID">
        <DashboardImpactCardTopUsers :from-date="fromDate" :to-date="toDate" :team-id="selectedTeam" />
      </Animate>
    </div>
  </div>
</template>
