<script setup lang="ts">
import { type CSSProperties } from 'vue';
import { UserTitleStatus } from '@/entities/title';

defineProps<{
  modelValue: UserTitleStatus;
  statuses: Array<{
    id: UserTitleStatus;
    label: string;
  }>;
}>();

defineEmits<{
  (e: 'update:modelValue', value: UserTitleStatus): void;
}>();

const statusColors: Record<UserTitleStatus, {
  rgb: string;
  textRgb: string;
  activeTextRgb: string;
  activeBg: string;
}> = {
  [UserTitleStatus.COMPLETED]: {
    rgb: '34 197 94',
    textRgb: '34 197 94',
    activeTextRgb: '255 255 255',
    activeBg: 'var(--status-active-bg)',
  },
  [UserTitleStatus.PLAYING]: {
    rgb: '59 130 246',
    textRgb: '59 130 246',
    activeTextRgb: '255 255 255',
    activeBg: 'var(--status-active-bg)',
  },
  [UserTitleStatus.WATCHING]: {
    rgb: '14 165 233',
    textRgb: '14 165 233',
    activeTextRgb: '255 255 255',
    activeBg: 'var(--status-active-bg)',
  },
  [UserTitleStatus.DROPPED]: {
    rgb: '239 68 68',
    textRgb: '239 68 68',
    activeTextRgb: '255 255 255',
    activeBg: 'var(--status-active-bg)',
  },
  [UserTitleStatus.PLANNED]: {
    rgb: '241 245 249',
    textRgb: '51 65 85',
    activeTextRgb: '51 65 85',
    activeBg: '0.96',
  },
  [UserTitleStatus.ON_HOLD]: {
    rgb: '249 115 22',
    textRgb: '234 88 12',
    activeTextRgb: '255 255 255',
    activeBg: 'var(--status-active-bg)',
  },
};

const statusColorStyle = (status: UserTitleStatus): CSSProperties => {
  const color = statusColors[status];
  return {
    '--status-rgb': color.rgb,
    '--status-text-rgb': color.textRgb,
    '--status-active-text-rgb': color.activeTextRgb,
    '--status-active-bg-value': color.activeBg,
  } as CSSProperties;
};
</script>

<template>
  <div class="space-y-4 pb-5">
    <div class="flex flex-wrap gap-2">
      <button
        v-for="statusOption in statuses"
        :key="statusOption.id"
        class="status-button min-h-11 rounded-full px-3 py-1.5 text-sm font-medium"
        :class="{ 'status-button--active': modelValue === statusOption.id }"
        :style="statusColorStyle(statusOption.id)"
        :data-status="statusOption.id"
        @click="$emit('update:modelValue', statusOption.id)"
      >
        {{ statusOption.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.status-button {
  color: rgb(var(--status-text-rgb));
  background-color: rgb(var(--status-rgb) / var(--status-idle-bg));
  border: 1px solid rgb(var(--status-rgb) / var(--status-idle-border));
  transition:
    background-color 250ms ease,
    border-color 250ms ease,
    box-shadow 250ms ease,
    color 250ms ease,
    transform 250ms ease;
}

.status-button:hover {
  background-color: rgb(var(--status-rgb) / var(--status-hover-bg));
  border-color: rgb(var(--status-rgb) / var(--status-hover-border));
}

.status-button--active {
  color: rgb(var(--status-active-text-rgb));
  background-color: rgb(var(--status-rgb) / var(--status-active-bg-value));
  border-color: rgb(var(--status-rgb));
  box-shadow: 0 8px 20px rgb(var(--status-rgb) / var(--status-active-shadow));
}

.status-button--active:hover {
  transform: translateY(-1px);
}

.status-button[data-status="planned"] {
  color: var(--planned-status-text);
  border-color: var(--planned-status-border);
}

.status-button[data-status="planned"]:hover {
  border-color: var(--planned-status-hover-border);
}

.status-button--active[data-status="planned"] {
  color: var(--planned-status-active-text);
  border-color: rgb(var(--status-rgb));
}

:global(:root),
:global([data-theme="light"]) {
  --status-idle-bg: 0.1;
  --status-idle-border: 0.28;
  --status-hover-bg: 0.16;
  --status-hover-border: 0.42;
  --status-active-bg: 0.92;
  --status-active-shadow: 0.22;
  --planned-status-text: rgb(51 65 85);
  --planned-status-active-text: rgb(51 65 85);
  --planned-status-border: rgb(148 163 184);
  --planned-status-hover-border: rgb(100 116 139);
}

:global([data-theme="dark"]) {
  --status-idle-bg: 0.12;
  --status-idle-border: 0.32;
  --status-hover-bg: 0.18;
  --status-hover-border: 0.5;
  --status-active-bg: 0.72;
  --status-active-shadow: 0.18;
  --planned-status-text: rgb(226 232 240);
  --planned-status-active-text: rgb(30 41 59);
  --planned-status-border: rgb(148 163 184 / 0.55);
  --planned-status-hover-border: rgb(203 213 225 / 0.75);
}

:global([data-theme="midnight"]) {
  --status-idle-bg: 0.14;
  --status-idle-border: 0.36;
  --status-hover-bg: 0.2;
  --status-hover-border: 0.54;
  --status-active-bg: 0.64;
  --status-active-shadow: 0.18;
  --planned-status-text: rgb(226 232 240);
  --planned-status-active-text: rgb(30 41 59);
  --planned-status-border: rgb(148 163 184 / 0.55);
  --planned-status-hover-border: rgb(203 213 225 / 0.75);
}
</style>
