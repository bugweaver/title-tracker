<script setup lang="ts">
import { computed, ref } from 'vue';
import { useTheme } from '@/shared/composables';

const { themes, resolvedTheme, theme, activeTheme, setTheme, previewTheme } = useTheme();

const query = ref('');

const filteredThemes = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return themes;
  return themes.filter(
    (t) => t.name.toLowerCase().includes(q) || t.id.toLowerCase().includes(q),
  );
});

const currentLabel = computed(() => {
  if (theme.value === 'system') return `Как в системе → ${activeTheme.value.name}`;
  return activeTheme.value.name;
});

function selectTheme(id: string) {
  previewTheme(null);
  setTheme(id);
}

function onPreviewEnter(id: string) {
  previewTheme(id);
}

function onPreviewLeave() {
  previewTheme(null);
}
</script>

<template>
  <div class="rounded-xl border border-border bg-background-soft px-4 py-6 sm:px-6 sm:py-8">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 class="text-xl font-bold text-text">Тема</h2>
        <p class="mt-1 text-sm text-text-secondary">
          Наведите для превью, кликните чтобы применить.
          Сейчас:
          <span class="font-medium text-text">{{ currentLabel }}</span>
        </p>
      </div>
      <label class="flex w-full flex-col gap-1.5 sm:w-56">
        <span class="sr-only">Поиск темы</span>
        <input
          v-model="query"
          type="search"
          placeholder="Поиск…"
          class="min-h-11 rounded-lg border border-border bg-background px-3 text-text outline-none transition-colors focus:border-primary-500"
        />
      </label>
    </div>

    <div class="flex flex-wrap gap-2" style="margin-top: 1.25rem; margin-bottom: 1.25rem">
      <button
        type="button"
        class="min-h-10 rounded-lg border px-3 text-sm transition-colors"
        :class="theme === 'system'
          ? 'border-primary-500 bg-primary-500/10 text-primary-500'
          : 'border-border text-text-secondary hover:bg-surface-hover hover:text-text'"
        @click="setTheme('system')"
      >
        Как в системе
      </button>
    </div>

    <div
      class="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5"
      @mouseleave="onPreviewLeave"
    >
      <button
        v-for="item in filteredThemes"
        :key="item.id"
        type="button"
        class="group relative flex flex-col overflow-hidden rounded-xl border text-left transition-all"
        :class="resolvedTheme === item.id && theme !== 'system'
          ? 'border-primary-500 ring-2 ring-primary-500/30'
          : 'border-border hover:border-border-hover'"
        :aria-pressed="resolvedTheme === item.id"
        @click="selectTheme(item.id)"
        @mouseenter="onPreviewEnter(item.id)"
        @focus="onPreviewEnter(item.id)"
        @blur="onPreviewLeave"
      >
        <div
          class="flex h-14 items-end gap-1 px-3 pb-2 pt-3"
          :style="{ background: item.bg }"
        >
          <span
            class="h-6 w-6 rounded-md shadow-sm"
            :style="{ background: item.primary }"
          />
          <span
            class="h-6 flex-1 rounded-md"
            :style="{ background: item.surface, border: `1px solid ${item.textMuted}33` }"
          />
          <span
            class="mb-0.5 h-2 w-8 rounded-sm"
            :style="{ background: item.text }"
          />
        </div>
        <div
          class="flex items-center justify-between gap-2 px-3 py-2"
          :style="{ background: item.bgSoft, color: item.text }"
        >
          <span class="truncate text-sm font-medium">{{ item.name }}</span>
          <span
            class="shrink-0 text-[10px] uppercase tracking-wide opacity-60"
          >{{ item.mode }}</span>
        </div>
      </button>
    </div>

    <p v-if="filteredThemes.length === 0" class="mt-3 text-sm text-text-muted">
      Ничего не найдено
    </p>
  </div>
</template>
