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
  <div class="game-review-header p-6 flex gap-6 items-start">
    <div class="w-24 h-36 bg-[var(--color-background-mute)] rounded-lg shadow-md flex-shrink-0 overflow-hidden">
      <img v-if="title.poster_url" :src="title.poster_url" class="w-full h-full object-cover" />
      <div v-else class="w-full h-full flex items-center justify-center text-[var(--color-text-muted)] text-xs">No Img</div>
    </div>

    <div class="flex-1">
      <div class="flex justify-between items-start mb-2">
        <h2 class="text-xl font-bold text-[var(--color-text)] leading-tight">{{ title.title }}</h2>
        <div v-if="status !== UserTitleStatus.PLANNED" class="flex flex-col items-center ml-2">
          <span class="game-review-score text-3xl font-black min-w-[3rem] text-center">
            {{ rating === 0 ? '-' : (rating === 10 ? '10' : rating.toFixed(1)) }}
          </span>
          <span class="text-2xl">{{ emoji }}</span>
        </div>
      </div>
      <p class="text-[var(--color-text-secondary)] text-sm">
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
