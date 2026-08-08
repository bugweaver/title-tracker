<script setup lang="ts">
import { computed } from 'vue';
import { Search, X } from 'lucide-vue-next';
import { AppSelect } from '@/shared/ui';
import {
  PLATFORM_FILTER_OPTIONS,
  SCORE_FILTER_OPTIONS,
  type LibraryFilterState,
} from '../composables/useLibraryFilters';
import { GamePlatform } from '@/entities/title';

const filters = defineModel<LibraryFilterState>('filters', { required: true });

const props = defineProps<{
  genres: string[];
  releaseYears: number[];
  showPlatform?: boolean;
  hasActiveFilters?: boolean;
}>();

const emit = defineEmits<{
  reset: [];
}>();

const genreOptions = computed(() => [
  { value: null, label: 'Все жанры' },
  ...props.genres.map((genre) => ({ value: genre, label: genre })),
]);

const releaseYearOptions = computed(() => [
  { value: null, label: 'Год выхода' },
  ...props.releaseYears.map((year) => ({ value: year, label: String(year) })),
]);
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="relative">
      <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
      <input
        v-model="filters.search"
        type="search"
        placeholder="Поиск по библиотеке..."
        class="min-h-11 w-full rounded-lg border border-border bg-surface py-2 pl-10 pr-10 text-sm text-text outline-none transition-colors placeholder:text-text-muted focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
      />
      <button
        v-if="filters.search"
        type="button"
        class="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-text-muted transition-colors hover:bg-background-soft hover:text-text"
        aria-label="Очистить поиск"
        @click="filters.search = ''"
      >
        <X class="h-4 w-4" />
      </button>
    </div>

    <div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
      <AppSelect
        v-model="filters.genre"
        :options="genreOptions"
        placeholder="Все жанры"
        class="min-w-0"
      />
      <AppSelect
        v-model="filters.releaseYear"
        :options="releaseYearOptions"
        placeholder="Год выхода"
        class="min-w-0"
      />
      <AppSelect
        v-if="showPlatform"
        v-model="filters.platform"
        :options="PLATFORM_FILTER_OPTIONS as { value: GamePlatform | null; label: string }[]"
        placeholder="Все платформы"
        class="min-w-0"
      />
      <AppSelect
        v-model="filters.minScore"
        :options="SCORE_FILTER_OPTIONS"
        placeholder="Любая оценка"
        class="min-w-0"
      />
      <div class="col-span-2 flex flex-wrap items-center gap-2 sm:col-span-1 lg:col-span-1">
        <button
          type="button"
          class="min-h-10 rounded-full px-3 py-1.5 text-sm font-medium transition-colors"
          :class="filters.hasReview
            ? 'bg-primary-100 text-primary-700'
            : 'bg-background-soft text-text-secondary hover:text-text'"
          @click="filters.hasReview = !filters.hasReview"
        >
          Есть отзыв
        </button>
        <button
          type="button"
          class="min-h-10 rounded-full px-3 py-1.5 text-sm font-medium transition-colors"
          :class="filters.hasScreenshots
            ? 'bg-primary-100 text-primary-700'
            : 'bg-background-soft text-text-secondary hover:text-text'"
          @click="filters.hasScreenshots = !filters.hasScreenshots"
        >
          Есть скрины
        </button>
        <button
          v-if="hasActiveFilters"
          type="button"
          class="min-h-10 text-sm text-text-muted underline-offset-2 hover:text-text hover:underline"
          @click="emit('reset')"
        >
          Сбросить
        </button>
      </div>
    </div>
  </div>
</template>
