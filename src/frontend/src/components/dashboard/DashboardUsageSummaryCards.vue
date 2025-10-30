<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { ref, onMounted, computed, watch } from 'vue';
import { UsageSummary, MY_TEAM_ID } from '@/services/api';
import { ApiService } from '@/services/api';
import { useErrorHandler } from '@/composables/useErrorHandler';
import { useNumberFormatter } from '@/composables/useNumberFormatter';
import { AnimationEffect } from '@tero/common/utils/animations.js';
import { usePercentageComparison } from '@/composables/usePercentageComparison';

const { t } = useI18n();
const { handleError } = useErrorHandler();
const { formatCompactNumber } = useNumberFormatter();
const api = new ApiService();

const props = defineProps<{
    fromDate: Date;
    toDate: Date;
    teamId: number;
}>();

const loading = ref<boolean>(false);
const metrics = ref<UsageSummary>();
const activeUsers = ref<number>(0);
const totalChats = ref<number>(0);

const { previousPercentageComparison } = usePercentageComparison();

const previousMonthComparisonActiveUsers = computed(() => {
    return metrics.value ? previousPercentageComparison(activeUsers.value, metrics.value?.previousActiveUsers) : 0;
})

const previousMonthComparisonTotalChats = computed(() => {
    return metrics.value ? previousPercentageComparison(totalChats.value, metrics.value?.previousTotalThreads) : 0;
})

const cards = computed(() => [
    ...(props.teamId !== MY_TEAM_ID ? [{
        title: t('activeUsersTitle'),
        icon: 'IconUser',
        tooltip: t('activeUsersTooltip'),
        value: formatCompactNumber(activeUsers.value as number),
        previousMonthComparison: previousMonthComparisonActiveUsers.value,
        previousMonthComparisonTitle: t('sinceLastMonth'),
        comparisonUnit: '%'
    }] : []),
    {
        title: t('totalChatsTitle'),
        icon: 'IconMessages',
        tooltip: t('totalChatsTooltip'),
        value: formatCompactNumber(totalChats.value as number),
        previousMonthComparison: previousMonthComparisonTotalChats.value,
        previousMonthComparisonTitle: t('sinceLastMonth'),
        comparisonUnit: '%'
    }
]);

onMounted(async () => {
    await loadSummaryData();
})

const loadSummaryData = async () => {
    try{
        loading.value = true;
        await loadData();
    } catch (error) {
        handleError(error);
    } finally {
        loading.value = false;
    }
}

const loadData = async () => {
    try {
        const data = await api.getUsageSummary(props.fromDate, props.toDate, props.teamId);
        metrics.value = data;
        activeUsers.value = data.activeUsers;
        totalChats.value = data.totalThreads;

    } catch (error) {
        handleError(error);
    }
}

watch(() => props.teamId, async () => {
    await loadSummaryData();
});

</script>

<template>
    <DashboardSummaryCardsLayout :loading="loading" :number-of-cards="2">
        <template v-for="(card, index) in cards" :key="index">
            <Animate :effect="AnimationEffect.SLIDE_DOWN_SPRING" :index="index"  :class="props.teamId !== MY_TEAM_ID ? 'w-1/2' : 'w-full'">
                <DashboardSummaryCard
                    :key="index"
                    class="h-full"
                    :title="card.title"
                    :icon="card.icon"
                    v-tooltip.bottom="card.tooltip">
                    <template #value>
                        <span class="cursor-default">
                            {{ card.value }}
                        </span>
                    </template>
                    <template #previousMonthComparison>
                        <div class="flex items-center gap-2">
                            <span class="flex items-center gap-1">
                                <IconCaretUpFilled v-if="card.previousMonthComparison && card.previousMonthComparison > 0"
                                    class="text-success" size="16"/>
                                <IconCaretDownFilled v-else-if="card.previousMonthComparison && card.previousMonthComparison < 0"
                                    class="text-error" size="16"/>
                                {{ card.previousMonthComparison != 0 ? `${card.previousMonthComparison > 0 ? '+' : ''}${card.previousMonthComparison}${card.comparisonUnit}` : t('comparisonNoChange') }}
                                {{ card.previousMonthComparisonTitle }}
                            </span>
                        </div>
                    </template>
                </DashboardSummaryCard>
            </Animate>
        </template>
    </DashboardSummaryCardsLayout>
</template>

<i18n lang="json">{
    "en": {
        "activeUsersTitle": "Active users",
        "activeUsersTooltip": "Number of active users in the last 30 days",
        "totalChatsTitle": "Total chats",
        "totalChatsTooltip": "Total number of chats in the last 30 days",
        "comparisonNoChange": "No changes",
        "sinceLastMonth": "since last month"
    },
    "es": {
        "activeUsersTitle": "Usuarios activos",
        "activeUsersTooltip": "Número de usuarios activos en los últimos 30 días",
        "totalChatsTitle": "Total de chats",
        "totalChatsTooltip": "Número de chats en los últimos 30 días",
        "comparisonNoChange": "Sin cambios",
        "sinceLastMonth": "desde el último mes"
    }
}</i18n>
