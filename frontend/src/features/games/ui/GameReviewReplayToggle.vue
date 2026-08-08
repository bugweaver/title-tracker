<script setup lang="ts">
defineProps<{
  modelValue: boolean;
  label: string;
}>();

defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();
</script>

<template>
  <label class="replay-toggle flex items-center gap-3 p-4 rounded-xl cursor-pointer">
    <input
      type="checkbox"
      class="sr-only"
      :checked="modelValue"
      @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    />

    <span class="toggle-mark flex h-10 w-10 items-center justify-center rounded-full font-black text-sm">
      +1
    </span>

    <span class="flex flex-col">
      <span class="text-sm font-semibold text-[var(--color-text-primary)]">{{ label }}</span>
      <span class="text-xs text-[var(--color-text-secondary)]">
        Добавить ещё одно завершение и обновить дату.
      </span>
    </span>
  </label>
</template>

<style scoped>
.replay-toggle {
  background:
    linear-gradient(135deg, rgb(16 185 129 / var(--replay-toggle-glow)), transparent 62%),
    color-mix(in srgb, rgb(16 185 129) var(--replay-toggle-tint), var(--color-surface));
  border: 1px solid color-mix(in srgb, rgb(16 185 129) 34%, var(--color-border));
  transition: border-color 250ms ease, box-shadow 250ms ease, transform 250ms ease;
}

.replay-toggle:hover {
  border-color: rgb(16 185 129);
  transform: translateY(-1px);
}

.toggle-mark {
  color: var(--replay-toggle-mark-text);
  background: var(--replay-toggle-mark-bg);
  border: 1px solid rgb(16 185 129 / 0.55);
  box-shadow: 0 8px 18px rgb(16 185 129 / var(--replay-toggle-shadow));
}

input:not(:checked) + .toggle-mark {
  color: rgb(16 185 129);
  background: transparent;
  box-shadow: none;
}

:global(:root),
:global([data-theme-mode="light"]) {
  --replay-toggle-glow: 0.12;
  --replay-toggle-tint: 8%;
  --replay-toggle-shadow: 0.22;
  --replay-toggle-mark-bg: linear-gradient(135deg, #059669, #10b981);
  --replay-toggle-mark-text: white;
}

:global([data-theme-mode="dark"]) {
  --replay-toggle-glow: 0.18;
  --replay-toggle-tint: 12%;
  --replay-toggle-shadow: 0.28;
  --replay-toggle-mark-bg: linear-gradient(135deg, #059669, #34d399);
  --replay-toggle-mark-text: white;
}
</style>
