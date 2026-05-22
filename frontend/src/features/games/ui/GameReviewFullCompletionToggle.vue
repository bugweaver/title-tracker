<script setup lang="ts">
defineProps<{
  modelValue: boolean;
}>();

defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();
</script>

<template>
  <label class="full-completion-toggle flex items-center gap-3 p-4 rounded-xl cursor-pointer">
    <input
      type="checkbox"
      class="sr-only"
      :checked="modelValue"
      @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    />

    <span class="toggle-mark flex h-10 w-10 items-center justify-center rounded-full font-black text-sm">
      100%
    </span>

    <span class="flex flex-col">
      <span class="text-sm font-semibold text-[var(--color-text-primary)]">Пройдено на 100%</span>
      <span class="text-xs text-[var(--color-text-secondary)]">Для полного прохождения, всех достижений или коллекционных целей.</span>
    </span>
  </label>
</template>

<style scoped>
.full-completion-toggle {
  background:
    linear-gradient(135deg, rgb(124 58 237 / var(--completion-toggle-glow)), transparent 62%),
    color-mix(in srgb, rgb(124 58 237) var(--completion-toggle-tint), var(--color-surface));
  border: 1px solid color-mix(in srgb, rgb(168 85 247) 34%, var(--color-border));
  transition: border-color 250ms ease, box-shadow 250ms ease, transform 250ms ease;
}

.full-completion-toggle:hover {
  border-color: rgb(168 85 247);
  transform: translateY(-1px);
}

.toggle-mark {
  color: var(--completion-toggle-mark-text);
  background: var(--completion-toggle-mark-bg);
  border: 1px solid rgb(168 85 247 / 0.55);
  box-shadow: 0 8px 18px rgb(168 85 247 / var(--completion-toggle-shadow));
}

input:not(:checked) + .toggle-mark {
  color: rgb(168 85 247);
  background: transparent;
  box-shadow: none;
}

:global(:root),
:global([data-theme="light"]) {
  --completion-toggle-glow: 0.12;
  --completion-toggle-tint: 8%;
  --completion-toggle-shadow: 0.22;
  --completion-toggle-mark-bg: linear-gradient(135deg, #7c3aed, #d946ef);
  --completion-toggle-mark-text: white;
}

:global([data-theme="dark"]),
:global([data-theme="midnight"]) {
  --completion-toggle-glow: 0.18;
  --completion-toggle-tint: 12%;
  --completion-toggle-shadow: 0.28;
  --completion-toggle-mark-bg: linear-gradient(135deg, #8b5cf6, #d946ef);
  --completion-toggle-mark-text: white;
}
</style>
