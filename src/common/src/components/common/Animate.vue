<script lang="ts" setup>
import { ref, watch, computed, onMounted } from 'vue';
import { useMotion } from '@vueuse/motion';
import { AnimationEffect, animations } from "../../utils/animations"

const props = defineProps({
  effect: {
    type: String as () => AnimationEffect,
    default: AnimationEffect.SLIDE_IN_LEFT_SPRING
  },
  // Delay based on index
  index: {
    type: Number,
    default: 0
  },
  // Base delay for each item (in ms)
  baseDelay: {
    type: Number,
    default: 80
  },
  // Whether animation should be enabled
  enabled: {
    type: Boolean,
    default: true
  }
});

const shouldAnimate = ref(props.enabled);
const target = ref(null);

const selectedAnimation = computed(() => {
  return animations[props.effect];
});

const enterWithDelay = computed(() => {
  const delay = Math.max(0, props.index * props.baseDelay);
  const animation = selectedAnimation.value;
  
  return {
    ...animation.enter,
    transition: {
      ...(animation.enter.transition || {}),
      delay
    }
  };
});

const variants = computed(() => {
  const animation = selectedAnimation.value;
  return {
    initial: animation.initial,
    enter: enterWithDelay.value,
    leave: 'leave' in animation ? animation.leave : animation.initial
  };
});

const { apply } = useMotion(target, variants.value);
onMounted(() => {
  if (shouldAnimate.value) {
    setTimeout(() => {
      apply('enter');
    }, 20);
  }
});

watch(() => props.enabled, (newValue) => {
  shouldAnimate.value = newValue;
  if (newValue) {
    setTimeout(() => {
      apply('enter');
    }, 20);
  } else {
    apply('leave');
  }
}, { immediate: true });

const reset = () => {
  shouldAnimate.value = false;
  setTimeout(() => {
    shouldAnimate.value = true;
  }, 50);
};

defineExpose({
  reset
});
</script>

<template>
  <div ref="target" :class="shouldAnimate ? 'transform-gpu' : 'hidden'">
    <slot></slot>
  </div>
</template> 