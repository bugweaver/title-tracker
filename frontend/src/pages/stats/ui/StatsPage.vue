<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { statsApi, type YearStats } from '@/shared/api/stats';
import type { ApiError } from '@/shared/api';
import { AppSelect } from '@/shared/ui';
import { useTitleStore } from '@/entities/title';

const titleStore = useTitleStore();
const isLoading = ref(false);
const error = ref<string | null>(null);
const stats = ref<YearStats | null>(null);
const selectedYear = ref<number | null>(new Date().getFullYear());
const selectedMonth = ref<number | null>(null);

const MONTH_LABELS_SHORT = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
const MONTH_LABELS_FULL = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
];

const availableYears = computed(() => {
  const years = new Set<number>([new Date().getFullYear()]);
  titleStore.titles.forEach((title) => {
    if (title.finished_at) {
      years.add(new Date(title.finished_at).getFullYear());
    }
  });
  return Array.from(years).sort((a, b) => b - a);
});

const yearOptions = computed(() =>
  availableYears.value.map((year) => ({ value: year as number | null, label: String(year) })),
);

const monthOptions = computed(() => [
  { value: null, label: 'Весь год' },
  ...MONTH_LABELS_FULL.map((label, index) => ({
    value: index + 1 as number | null,
    label,
  })),
]);

const periodLabel = computed(() => {
  if (selectedMonth.value) {
    return `${MONTH_LABELS_FULL[selectedMonth.value - 1]} ${selectedYear.value}`;
  }
  return `${selectedYear.value} год`;
});

const emptyPeriodLabel = computed(() =>
  selectedMonth.value ? 'за этот месяц' : 'за этот год',
);

const maxMonthCount = computed(() =>
  Math.max(1, ...(stats.value?.monthly_heatmap.map((item) => item.count) || [1])),
);

const maxDayCount = computed(() =>
  Math.max(1, ...(stats.value?.daily_heatmap.map((item) => item.count) || [1])),
);

const maxPlatformCount = computed(() =>
  Math.max(1, ...(stats.value?.by_platform.map((item) => item.count) || [1])),
);

const maxCategoryCount = computed(() =>
  Math.max(1, ...(stats.value?.by_category.map((item) => item.count) || [1])),
);

const maxGenreCount = computed(() =>
  Math.max(1, ...(stats.value?.top_genres.map((item) => item.count) || [1])),
);

const heatmapIntensity = (count: number, maxCount: number) => {
  if (count <= 0) return 0;
  return Math.max(0.18, count / maxCount);
};

const selectMonthFromHeatmap = (month: number) => {
  selectedMonth.value = selectedMonth.value === month ? null : month;
};

const loadStats = async () => {
  const year = selectedYear.value ?? new Date().getFullYear();
  selectedYear.value = year;
  isLoading.value = true;
  error.value = null;
  try {
    stats.value = await statsApi.getYearStats(year, selectedMonth.value);
  } catch (e) {
    const apiError = e as ApiError;
    error.value = apiError.detail || 'Не удалось загрузить статистику';
    stats.value = null;
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  if (!titleStore.titles.length) {
    await titleStore.fetchMyTitles();
  }
  await loadStats();
});

watch([selectedYear, selectedMonth], () => {
  loadStats();
});
</script>

<template>
  <div class="mx-auto flex max-w-screen-xl flex-col gap-6 p-3 sm:gap-8 sm:p-6 lg:p-8">
    <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-text sm:text-3xl">Статистика</h1>
        <p class="mt-1 text-sm text-text-secondary">
          {{ periodLabel }} в цифрах по вашей библиотеке
        </p>
      </div>
      <div class="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto">
        <AppSelect
          v-model="selectedYear"
          :options="yearOptions"
          class="min-w-0 sm:w-32"
        />
        <AppSelect
          v-model="selectedMonth"
          :options="monthOptions"
          class="min-w-0 sm:w-40"
        />
      </div>
    </header>

    <div v-if="isLoading" class="flex justify-center p-16">
      <div class="h-8 w-8 animate-spin rounded-full border-b-2 border-primary-500"></div>
    </div>

    <div
      v-else-if="error"
      class="rounded-xl border border-border bg-surface px-4 py-10 text-center text-text-secondary"
    >
      {{ error }}
    </div>

    <template v-else-if="stats">
      <section class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div class="rounded-xl border border-border bg-surface p-4 sm:p-5">
          <p class="text-sm text-text-muted">Пройдено</p>
          <p class="mt-2 text-3xl font-bold text-text">{{ stats.completed_count }}</p>
        </div>
        <div class="rounded-xl border border-border bg-surface p-4 sm:p-5">
          <p class="text-sm text-text-muted">Средний балл</p>
          <p class="mt-2 text-3xl font-bold text-text">
            {{ stats.average_score !== null ? stats.average_score.toFixed(1) : '—' }}
          </p>
        </div>
        <div class="rounded-xl border border-border bg-surface p-4 sm:p-5">
          <p class="text-sm text-text-muted">Жанров в топе</p>
          <p class="mt-2 text-3xl font-bold text-text">{{ stats.top_genres.length }}</p>
        </div>
        <div class="rounded-xl border border-border bg-surface p-4 sm:p-5">
          <p class="text-sm text-text-muted">Категорий</p>
          <p class="mt-2 text-3xl font-bold text-text">{{ stats.by_category.length }}</p>
        </div>
      </section>

      <section class="rounded-xl border border-border bg-surface p-4 sm:p-6">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-lg font-semibold text-text">Активность по месяцам</h2>
          <p class="text-xs text-text-muted">Нажмите на месяц, чтобы открыть его статистику</p>
        </div>
        <div class="grid grid-cols-3 gap-2 sm:grid-cols-6 lg:grid-cols-12">
          <button
            v-for="item in stats.monthly_heatmap"
            :key="item.month"
            type="button"
            class="flex flex-col items-center gap-2 rounded-lg outline-none transition-transform hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-primary-500/40"
            @click="selectMonthFromHeatmap(item.month)"
          >
            <div
              class="heatmap-cell flex h-16 w-full items-center justify-center rounded-lg border"
              :class="selectedMonth === item.month
                ? 'border-primary-500 ring-2 ring-primary-500/30'
                : 'border-border'"
              :style="{
                background: item.count
                  ? `color-mix(in srgb, var(--color-primary-500) ${Math.round(heatmapIntensity(item.count, maxMonthCount) * 100)}%, var(--color-background-soft))`
                  : 'var(--color-background-soft)',
              }"
            >
              <span class="text-sm font-semibold text-text">{{ item.count || '' }}</span>
            </div>
            <span
              class="text-xs"
              :class="selectedMonth === item.month ? 'font-medium text-primary-500' : 'text-text-muted'"
            >
              {{ MONTH_LABELS_SHORT[item.month - 1] }}
            </span>
          </button>
        </div>
      </section>

      <section
        v-if="selectedMonth && stats.daily_heatmap.length"
        class="rounded-xl border border-border bg-surface p-4 sm:p-6"
      >
        <h2 class="mb-4 text-lg font-semibold text-text">
          Активность по дням · {{ MONTH_LABELS_FULL[selectedMonth - 1] }}
        </h2>
        <div class="grid grid-cols-7 gap-1.5 sm:gap-2">
          <div
            v-for="item in stats.daily_heatmap"
            :key="item.day"
            class="flex flex-col items-center gap-1"
          >
            <div
              class="flex aspect-square w-full items-center justify-center rounded-md border border-border text-xs font-semibold text-text sm:text-sm"
              :style="{
                background: item.count
                  ? `color-mix(in srgb, var(--color-primary-500) ${Math.round(heatmapIntensity(item.count, maxDayCount) * 100)}%, var(--color-background-soft))`
                  : 'var(--color-background-soft)',
              }"
              :title="`${item.day}: ${item.count}`"
            >
              {{ item.count || '' }}
            </div>
            <span class="text-[10px] text-text-muted sm:text-xs">{{ item.day }}</span>
          </div>
        </div>
      </section>

      <section class="grid gap-4 lg:grid-cols-2">
        <div class="rounded-xl border border-border bg-surface p-4 sm:p-6">
          <h2 class="mb-4 text-lg font-semibold text-text">Топ жанров</h2>
          <div v-if="stats.top_genres.length" class="flex flex-col gap-3">
            <div v-for="genre in stats.top_genres" :key="genre.name" class="flex flex-col gap-1">
              <div class="flex items-center justify-between text-sm">
                <span class="text-text">{{ genre.name }}</span>
                <span class="text-text-muted">{{ genre.count }}</span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-background-soft">
                <div
                  class="h-full rounded-full bg-primary-500 transition-all"
                  :style="{ width: `${(genre.count / maxGenreCount) * 100}%` }"
                />
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-text-muted">Пока нет данных {{ emptyPeriodLabel }}</p>
        </div>

        <div class="rounded-xl border border-border bg-surface p-4 sm:p-6">
          <h2 class="mb-4 text-lg font-semibold text-text">По категориям</h2>
          <div v-if="stats.by_category.length" class="flex flex-col gap-3">
            <div
              v-for="category in stats.by_category"
              :key="category.name"
              class="flex flex-col gap-1"
            >
              <div class="flex items-center justify-between text-sm">
                <span class="text-text">{{ category.name }}</span>
                <span class="text-text-muted">{{ category.count }}</span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-background-soft">
                <div
                  class="h-full rounded-full bg-emerald-500 transition-all"
                  :style="{ width: `${(category.count / maxCategoryCount) * 100}%` }"
                />
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-text-muted">Пока нет данных {{ emptyPeriodLabel }}</p>
        </div>
      </section>

      <section class="rounded-xl border border-border bg-surface p-4 sm:p-6">
        <h2 class="mb-4 text-lg font-semibold text-text">По платформам</h2>
        <div v-if="stats.by_platform.length" class="flex flex-col gap-3">
          <div
            v-for="platform in stats.by_platform"
            :key="platform.name"
            class="flex flex-col gap-1"
          >
            <div class="flex items-center justify-between text-sm">
              <span class="text-text">{{ platform.name }}</span>
              <span class="text-text-muted">{{ platform.count }}</span>
            </div>
            <div class="h-2 overflow-hidden rounded-full bg-background-soft">
              <div
                class="h-full rounded-full bg-sky-500 transition-all"
                :style="{ width: `${(platform.count / maxPlatformCount) * 100}%` }"
              />
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-text-muted">
          Нет игр с указанной платформой {{ emptyPeriodLabel }}
        </p>
      </section>
    </template>
  </div>
</template>
