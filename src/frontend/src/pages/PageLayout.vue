<script lang="ts" setup>
import { AnimationEffect } from '../../../common/src/utils/animations';
defineProps<{
    leftColumnClass?: string
    rightColumnClass?: string
}>()
</script>

<template>
     <div class="flex flex-col h-screen w-full">
        <div class="flex flex-row flex-1 p-2 sm:p-4 lg:p-6 gap-3 overflow-hidden relative">
            <Animate
                :effect="AnimationEffect.SLIDE_IN_LEFT"
                class="relative z-20 flex-shrink-0"
                :class="leftColumnClass">
                <slot name="left" />
            </Animate>
            <Animate
                :effect="AnimationEffect.SLIDE_IN_RIGHT"
                class="relative flex-1 z-20 min-w-0"
                :class="rightColumnClass">
                <slot name="right" />
            </Animate>
        </div>
    </div>
</template>
