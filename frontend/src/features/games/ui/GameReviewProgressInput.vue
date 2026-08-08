<script setup lang="ts">
defineProps<{
  label: string;
  modelValue: number | null;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: number | null];
}>();

const onInput = (event: Event) => {
  const raw = (event.target as HTMLInputElement).value;
  if (raw === '') {
    emit('update:modelValue', null);
    return;
  }
  const parsed = Number.parseInt(raw, 10);
  emit('update:modelValue', Number.isNaN(parsed) || parsed < 0 ? null : parsed);
};
</script>

<template>
  <div>
    <label class="mb-2 block text-sm font-medium text-[var(--color-text-secondary)]">
      {{ label }}
    </label>
    <input
      type="number"
      min="0"
      step="1"
      class="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-text outline-none transition-colors focus:border-primary-500"
      :value="modelValue ?? ''"
      :placeholder="label"
      @input="onInput"
    />
  </div>
</template>
