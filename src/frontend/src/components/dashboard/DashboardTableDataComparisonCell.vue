<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useNumberFormatter } from '@/composables/useNumberFormatter';

const { t } = useI18n();

const { previousValue, currentValue, valueTooltip, icon, iconClass, numberDecimals = 1, unit } = defineProps<{
    previousValue: number;
    currentValue: number;
    valueTooltip: string;
    icon: string;
    iconClass?: string;
    numberDecimals?: number;
    unit?: string;
    compactNumber?: boolean;
}>();

const { formatCompactNumber } = useNumberFormatter();
</script>

<template>
    <component :is="icon" :class="iconClass" class="w-5 h-5"/>
    <span class="flex items-center gap-1 font-medium translate-y-[.5px]">
        <IconCaretUpFilled v-if="previousValue < currentValue"
            class="text-success" size="16"
            v-tooltip.bottom="`+${(currentValue - previousValue).toFixed(numberDecimals)} ${t('sinceLastMonth')}`" />
        <IconCaretDownFilled v-else-if="previousValue > currentValue" class="text-error" size="16"
            v-tooltip.bottom="`-${(previousValue - currentValue).toFixed(numberDecimals)} ${t('sinceLastMonth')}`" />
        <span v-tooltip.bottom="valueTooltip">
            {{ compactNumber ? formatCompactNumber(currentValue, numberDecimals) : currentValue }}{{ unit }}
        </span>
    </span>
</template>

<i18n lang="json">
    {
        "en":{
            "sinceLastMonth": "since last month"
        },
        "es":{
            "sinceLastMonth": "desde el último mes"
        }
    }
</i18n>
