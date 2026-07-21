<script setup lang="ts">
import { type TitleSearchResult } from '@/shared/api/titles';
import { UserTitleStatus } from '@/entities/title';

defineProps<{
  title: TitleSearchResult;
  status: UserTitleStatus;
  rating: number;
  emoji: string;
}>();
</script>

<template>
  <div class="game-review-header flex items-start gap-4 px-4 pb-4 pt-[calc(1rem+env(safe-area-inset-top))] sm:gap-6 sm:p-6">
    <div class="h-24 w-16 flex-shrink-0 overflow-hidden rounded-lg bg-[var(--color-background-mute)] shadow-md sm:h-36 sm:w-24">
      <img v-if="title.poster_url" :src="title.poster_url" class="w-full h-full object-cover" />
      <div v-else class="w-full h-full flex items-center justify-center text-[var(--color-text-muted)] text-xs">No Img</div>
    </div>

    <div class="min-w-0 flex-1">
      <div class="flex justify-between items-start mb-2">
        <h2 class="break-words text-lg font-bold leading-tight text-[var(--color-text)] sm:text-xl">{{ title.title }}</h2>
        <div v-if="status !== UserTitleStatus.PLANNED" class="flex flex-col items-center ml-2">
          <span class="game-review-score min-w-[2.5rem] text-center text-2xl font-black sm:min-w-[3rem] sm:text-3xl">
            {{ rating === 0 ? '-' : (rating === 10 ? '10' : rating.toFixed(1)) }}
          </span>
          <span class="text-xl sm:text-2xl">{{ emoji }}</span>
        </div>
      </div>
      <p class="line-clamp-3 text-xs text-[var(--color-text-secondary)] sm:text-sm">
        {{ title.release_year }}
        <span v-if="title.genres && title.genres.length">• {{ title.genres.join(', ') }}</span>
      </p>
    </div>
  </div>
</template>

<style scoped>
.game-review-header {
  background-color: rgb(var(--review-tone-rgb) / var(--review-header-tint, 0.1));
  border-bottom: 1px solid rgb(var(--review-tone-rgb) / 0.12);
  transition: background-color 450ms ease, border-color 450ms ease;
}

.game-review-score {
  color: rgb(var(--review-tone-rgb));
  transition: color 450ms ease;
}
</style>
