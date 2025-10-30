<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { ref, onMounted, computed, watch } from 'vue';
import { ImpactSummary } from '@/services/api';
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
const metrics = ref<ImpactSummary>();
const totalHours = ref<number>(0);
const impactRatio = ref<number>(0);

const { previousPercentageComparison } = usePercentageComparison();

const previousMonthComparisonAiHours = computed(() => {
    return metrics.value ? previousPercentageComparison(metrics.value?.aiHours, metrics.value?.previousAiHours) : 0;
})

const previousMonthComparisonHumanHours = computed(() => {
    return metrics.value ? previousPercentageComparison(metrics.value?.humanHours, metrics.value?.previousHumanHours) : 0;
})

const previousMonthComparisonTotalHours = computed(() => {
    if (!metrics.value) return 0;
    const totalHours = metrics.value?.aiHours + metrics.value?.humanHours;
    const previousTotalHours = metrics.value?.previousAiHours + metrics.value?.previousHumanHours;
    return previousPercentageComparison(totalHours, previousTotalHours);
})

const previousMonthComparisonAiImpact = computed(() => {
    if (!metrics.value) return 0;
    let previousImpactRatio = 1;
    if (metrics.value?.previousHumanHours !== 0)
        previousImpactRatio = (metrics.value?.previousAiHours + metrics.value?.previousHumanHours) / metrics.value?.previousHumanHours;
    const difference = impactRatio.value - previousImpactRatio;
    return parseFloat(difference.toFixed(2));
})

const cards = computed(() => [
    {
        title: t('IAHoursTitle'),
        icon: 'IconSparkles',
        tooltip: t('IAHoursTooltip'),
        value: formatCompactNumber(metrics.value?.aiHours as number),
        previousMonthComparison: previousMonthComparisonAiHours.value,
        previousMonthComparisonTitle: t('sinceLastMonth'),
        comparisonUnit: '%'
    },
    {
        title: t('humanHoursTitle'),
        icon: 'IconBrain',
        tooltip: t('humanHoursTooltip'),
        value: formatCompactNumber(metrics.value?.humanHours as number),
        previousMonthComparison: previousMonthComparisonHumanHours.value,
        previousMonthComparisonTitle: t('sinceLastMonth'),
        comparisonUnit: '%'
    },
    {
        title: t('totalHoursTitle'),
        icon: 'IconClock',
        tooltip: t('totalHoursTooltip'),
        value: formatCompactNumber(totalHours.value as number),
        previousMonthComparison: previousMonthComparisonTotalHours.value,
        previousMonthComparisonTitle: t('sinceLastMonth'),
        comparisonUnit: '%'
    },
    {
        title: t('IAImpactTitle'),
        icon: 'IconBoltFilled',
        tooltip: t('IAImpactTooltip'),
        value: `${impactRatio.value.toFixed(2)}x`,
        class: 'border-1 border-primary shadow-light',
        valueClass: 'text-primary',
        previousMonthComparison: previousMonthComparisonAiImpact.value,
        previousMonthComparisonTitle: t('sinceLastMonth'),
        comparisonUnit: 'x'
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
        const data = await api.getImpactSummary(props.fromDate, props.toDate, props.teamId);
        metrics.value = data;

        totalHours.value = data.humanHours + data.aiHours;
        impactRatio.value = totalHours.value / data.humanHours;
    } catch (error) {
        handleError(error);
    }
}

watch(() => props.teamId, async () => {
    await loadSummaryData();
});

</script>

<template>
    <DashboardSummaryCardsLayout :loading="loading" :number-of-cards="4">
        <template v-for="(card, index) in cards" :key="index">
            <Animate :effect="AnimationEffect.SLIDE_DOWN_SPRING" :index="index" class="w-1/4">
                <DashboardSummaryCard
                    :key="index"
                    :class="card.class"
                    class="h-full"
                    :title="card.title"
                    :icon="card.icon"
                    v-tooltip.bottom="card.tooltip">
                    <template #value>
                        <span class="cursor-default" :class="card.valueClass">
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
        "totalHoursTitle": "Total hours",
        "humanHoursTitle": "Human hours",
        "IAHoursTitle": "AI hours",
        "IAImpactTitle": "AI impact",
        "IAHoursTooltip": "Estimated total hours saved by all users while using agents in the last 30 days",
        "humanHoursTooltip": "Estimated total working hours for all users in the last 30 days",
        "totalHoursTooltip": "Estimated total hours of work done by humans in combination with AI in the last 30 days (AI hours + Human hours)",
        "IAImpactTooltip": "Estimated total impact factor of the use of AI in the last 30 days (AI hours + Human Hours / Human Hours)",
        "comparisonNoChange": "No changes",
        "sinceLastMonth": "since last month"
    },
    "es": {
        "totalHoursTitle": "Horas totales",
        "humanHoursTitle": "Horas humanas",
        "IAHoursTitle": "Horas IA",
        "IAImpactTitle": "Impacto IA",
        "IAHoursTooltip": "Horas totales estimadas ahorradas por todos los usuarios al usar agentes en los últimos 30 días",
        "humanHoursTooltip": "Horas totales estimadas de trabajo para todos los usuarios en los últimos 30 días",
        "totalHoursTooltip": "Horas totales estimadas de trabajo realizadas por humanos en combinación con IA en los últimos 30 días (horas de IA + horas humanas)",
        "IAImpactTooltip": "Factor de impacto estimado del uso de IA en los últimos 30 días (horas de IA + horas humanas / horas humanas)",
        "comparisonNoChange": "Sin cambios",
        "sinceLastMonth": "desde el último mes"
    }
}</i18n>
