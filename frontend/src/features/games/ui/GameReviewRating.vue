<script setup lang="ts">
defineProps<{
  modelValue: number;
}>();

defineEmits<{
  (e: 'update:modelValue', value: number): void;
}>();
</script>

<template>
  <div class="space-y-2 pb-2">
    <label class="text-sm font-medium text-[var(--color-text-secondary)]">Оценка</label>
    <input
      type="range"
      :value="modelValue"
      min="1"
      max="10"
      step="0.1"
      class="game-review-rating h-3 w-full cursor-pointer appearance-none rounded-lg"
      @input="$emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
    />
    <div class="flex justify-between text-xs text-[var(--color-text-muted)] px-1">
      <span>1.0</span>
      <span>5.0</span>
      <span>10.0</span>
    </div>
  </div>
</template>

<style scoped>
.game-review-rating {
  accent-color: rgb(var(--review-tone-rgb));
  background:
    linear-gradient(rgb(var(--review-tone-rgb)), rgb(var(--review-tone-rgb))) 0 / calc((v-bind(modelValue) - 1) / 9 * 100%) 100% no-repeat,
    var(--color-background-mute);
  transition: accent-color 450ms ease, background 450ms ease;
}

.game-review-rating::-webkit-slider-thumb {
  width: 28px;
  height: 28px;
  appearance: none;
  border: 3px solid var(--color-surface);
  border-radius: 9999px;
  background: rgb(var(--review-tone-rgb));
  box-shadow: 0 2px 8px rgb(0 0 0 / 0.28);
}

.game-review-rating::-moz-range-thumb {
  width: 24px;
  height: 24px;
  border: 3px solid var(--color-surface);
  border-radius: 9999px;
  background: rgb(var(--review-tone-rgb));
  box-shadow: 0 2px 8px rgb(0 0 0 / 0.28);
}
</style>
