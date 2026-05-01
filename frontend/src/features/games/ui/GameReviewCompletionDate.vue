<script setup lang="ts">
import AppSelect from '@/shared/ui/AppSelect.vue';

defineProps<{
  month: number | null;
  year: number | null;
  monthOptions: Array<{
    value: number;
    label: string;
  }>;
  yearOptions: Array<{
    value: number;
    label: string;
  }>;
}>();

defineEmits<{
  (e: 'update:month', value: number | null): void;
  (e: 'update:year', value: number | null): void;
}>();
</script>

<template>
  <div class="space-y-2 pb-2">
    <label class="text-sm font-medium text-[var(--color-text-secondary)]">Дата завершения</label>
    <div class="flex gap-2">
      <div class="w-1/2">
        <AppSelect
          :model-value="month"
          :options="monthOptions"
          placeholder="Месяц"
          @update:model-value="$emit('update:month', $event)"
        />
      </div>
      <div class="w-1/2">
        <AppSelect
          :model-value="year"
          :options="yearOptions"
          placeholder="Год"
          @update:model-value="$emit('update:year', $event)"
        />
      </div>
    </div>
  </div>
</template>
