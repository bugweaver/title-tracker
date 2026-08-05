<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue';
import {
  UserTitleStatus,
  type SeasonStructure,
  type SeriesStructure,
} from '@/entities/title';
import { titlesApi } from '@/shared/api/titles';
import GameReviewRating from './GameReviewRating.vue';
import GameReviewStatusSelector from './GameReviewStatusSelector.vue';
import GameReviewTextArea from './GameReviewTextArea.vue';

const props = defineProps<{
  userTitleId: number;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  (e: 'updated', structure: SeriesStructure): void;
}>();

const structure = ref<SeriesStructure | null>(null);
const isLoading = ref(false);
const expandedSeasons = ref<Set<number>>(new Set());
const loadingEpisodes = ref<Set<number>>(new Set());
const savingKey = ref<string | null>(null);
const localSeasonReviews = ref<Record<number, string>>({});
const debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();

const debounce = (key: string, fn: () => void, ms = 450) => {
  const existing = debounceTimers.get(key);
  if (existing) clearTimeout(existing);
  debounceTimers.set(
    key,
    setTimeout(() => {
      debounceTimers.delete(key);
      fn();
    }, ms),
  );
};

onUnmounted(() => {
  for (const timer of debounceTimers.values()) clearTimeout(timer);
  debounceTimers.clear();
});

const seasonStatuses = [
  { id: UserTitleStatus.COMPLETED, label: 'Посмотрел' },
  { id: UserTitleStatus.WATCHING, label: 'Смотрю' },
  { id: UserTitleStatus.DROPPED, label: 'Дропнул' },
  { id: UserTitleStatus.PLANNED, label: 'В планах' },
  { id: UserTitleStatus.ON_HOLD, label: 'На паузе' },
];

const episodeStatuses = [
  { id: UserTitleStatus.COMPLETED, label: 'Посмотрел' },
  { id: UserTitleStatus.WATCHING, label: 'Смотрю' },
  { id: UserTitleStatus.DROPPED, label: 'Дропнул' },
  { id: UserTitleStatus.PLANNED, label: 'В планах' },
  { id: UserTitleStatus.ON_HOLD, label: 'На паузе' },
];

const syncLocalReviews = (next: SeriesStructure) => {
  const reviews: Record<number, string> = {};
  for (const season of next.seasons) {
    reviews[season.season_number] = season.review_text || '';
  }
  localSeasonReviews.value = reviews;
};

const applyStructure = (next: SeriesStructure) => {
  structure.value = next;
  syncLocalReviews(next);
  emit('updated', next);
};

const loadStructure = async () => {
  if (!props.userTitleId) return;
  isLoading.value = true;
  try {
    const data = props.readonly
      ? await titlesApi.getPublicStructure(props.userTitleId)
      : await titlesApi.getStructure(props.userTitleId);
    structure.value = data;
    syncLocalReviews(data);
  } catch (error) {
    console.error('Failed to load series structure', error);
  } finally {
    isLoading.value = false;
  }
};

watch(
  () => props.userTitleId,
  () => {
    expandedSeasons.value = new Set();
    void loadStructure();
  },
  { immediate: true },
);

const toggleSeason = async (season: SeasonStructure) => {
  const number = season.season_number;
  if (expandedSeasons.value.has(number)) {
    expandedSeasons.value.delete(number);
    expandedSeasons.value = new Set(expandedSeasons.value);
    return;
  }

  expandedSeasons.value.add(number);
  expandedSeasons.value = new Set(expandedSeasons.value);

  if (!season.episodes_loaded) {
    loadingEpisodes.value.add(number);
    loadingEpisodes.value = new Set(loadingEpisodes.value);
    try {
      const updatedSeason = await titlesApi.syncSeasonEpisodes(
        props.userTitleId,
        number,
        props.readonly,
      );
      if (structure.value) {
        structure.value = {
          ...structure.value,
          seasons: structure.value.seasons.map((s) =>
            s.season_number === number ? { ...updatedSeason, episodes_loaded: true } : s,
          ),
        };
      }
    } catch (error) {
      console.error('Failed to sync season episodes', error);
    } finally {
      loadingEpisodes.value.delete(number);
      loadingEpisodes.value = new Set(loadingEpisodes.value);
    }
  }
};

const updateSeasonScore = (season: SeasonStructure, score: number) => {
  if (props.readonly) return;
  if (structure.value) {
    structure.value = {
      ...structure.value,
      seasons: structure.value.seasons.map((s) =>
        s.season_number === season.season_number
          ? { ...s, score: score || null, score_is_manual: Boolean(score) }
          : s,
      ),
    };
  }
  debounce(`season-score-${season.season_number}`, async () => {
    savingKey.value = `season-score-${season.season_number}`;
    try {
      const next = await titlesApi.updateSeason(props.userTitleId, season.season_number, {
        score: score || undefined,
        clear_score: !score,
        status: season.status ?? UserTitleStatus.WATCHING,
      });
      applyStructure(next);
    } catch (error) {
      console.error('Failed to update season score', error);
    } finally {
      savingKey.value = null;
    }
  });
};

const updateSeasonStatus = async (season: SeasonStructure, status: UserTitleStatus) => {
  if (props.readonly) return;
  savingKey.value = `season-status-${season.season_number}`;
  try {
    const next = await titlesApi.updateSeason(props.userTitleId, season.season_number, {
      status,
      score: season.score ?? undefined,
    });
    applyStructure(next);
  } catch (error) {
    console.error('Failed to update season status', error);
  } finally {
    savingKey.value = null;
  }
};

const updateSeasonReview = (season: SeasonStructure, reviewText: string) => {
  if (props.readonly) return;
  localSeasonReviews.value = {
    ...localSeasonReviews.value,
    [season.season_number]: reviewText,
  };
  debounce(`season-review-${season.season_number}`, async () => {
    savingKey.value = `season-review-${season.season_number}`;
    try {
      const next = await titlesApi.updateSeason(props.userTitleId, season.season_number, {
        review_text: reviewText,
        is_spoiler: /<[^<>]+>/.test(reviewText),
        status: season.status ?? UserTitleStatus.WATCHING,
        score: season.score ?? undefined,
      });
      applyStructure(next);
    } catch (error) {
      console.error('Failed to update season review', error);
    } finally {
      savingKey.value = null;
    }
  }, 700);
};

const resetSeasonScore = async (season: SeasonStructure) => {
  if (props.readonly) return;
  savingKey.value = `season-reset-${season.season_number}`;
  try {
    const next = await titlesApi.resetSeasonScore(props.userTitleId, season.season_number);
    applyStructure(next);
  } catch (error) {
    console.error('Failed to reset season score', error);
  } finally {
    savingKey.value = null;
  }
};

const updateEpisodeScore = (
  season: SeasonStructure,
  episodeNumber: number,
  score: number,
) => {
  if (props.readonly) return;
  if (structure.value) {
    structure.value = {
      ...structure.value,
      seasons: structure.value.seasons.map((s) =>
        s.season_number === season.season_number
          ? {
              ...s,
              episodes: s.episodes.map((ep) =>
                ep.episode_number === episodeNumber
                  ? { ...ep, score: score || null }
                  : ep,
              ),
            }
          : s,
      ),
    };
  }
  debounce(`ep-score-${season.season_number}-${episodeNumber}`, async () => {
    savingKey.value = `ep-score-${season.season_number}-${episodeNumber}`;
    try {
      const next = await titlesApi.updateEpisode(
        props.userTitleId,
        season.season_number,
        episodeNumber,
        { score: score || undefined, clear_score: !score },
      );
      applyStructure(next);
    } catch (error) {
      console.error('Failed to update episode score', error);
    } finally {
      savingKey.value = null;
    }
  });
};

const updateEpisodeStatus = async (
  season: SeasonStructure,
  episodeNumber: number,
  status: UserTitleStatus,
) => {
  if (props.readonly) return;
  savingKey.value = `ep-status-${season.season_number}-${episodeNumber}`;
  try {
    const next = await titlesApi.updateEpisode(
      props.userTitleId,
      season.season_number,
      episodeNumber,
      { status },
    );
    applyStructure(next);
  } catch (error) {
    console.error('Failed to update episode status', error);
  } finally {
    savingKey.value = null;
  }
};

const seasonLabel = (season: SeasonStructure) =>
  season.name?.trim() || `Сезон ${season.season_number}`;

const episodeLabel = (episodeNumber: number, name: string | null) =>
  name?.trim() ? `S${episodeNumber}: ${name}` : `Серия ${episodeNumber}`;
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between gap-2">
      <h3 class="text-sm font-medium text-[var(--color-text-secondary)]">Сезоны и серии</h3>
      <span v-if="isLoading" class="text-xs text-[var(--color-text-muted)]">Загрузка…</span>
    </div>

    <div v-if="!isLoading && structure && structure.seasons.length === 0" class="text-sm text-[var(--color-text-muted)]">
      Сезоны пока не найдены
    </div>

    <div
      v-for="season in structure?.seasons ?? []"
      :key="season.title_season_id"
      class="rounded-lg border border-[var(--color-border)] bg-[var(--color-background-soft)]/40"
    >
      <button
        type="button"
        class="flex w-full items-center justify-between gap-3 px-3 py-3 text-left"
        @click="toggleSeason(season)"
      >
        <div class="min-w-0">
          <div class="truncate text-sm font-medium text-[var(--color-text)]">
            {{ seasonLabel(season) }}
          </div>
          <div class="mt-0.5 text-xs text-[var(--color-text-muted)]">
            <span v-if="season.score != null">{{ season.score }}/10</span>
            <span v-if="season.score != null && season.avg_score != null && season.score_is_manual">
              · среднее {{ season.avg_score }}
            </span>
            <span v-else-if="season.score == null && season.avg_score != null">
              среднее {{ season.avg_score }}
            </span>
            <span v-if="season.episode_count"> · {{ season.episode_count }} сер.</span>
          </div>
        </div>
        <span class="shrink-0 text-[var(--color-text-muted)]">
          {{ expandedSeasons.has(season.season_number) ? '▾' : '▸' }}
        </span>
      </button>

      <div
        v-if="expandedSeasons.has(season.season_number)"
        class="space-y-4 border-t border-[var(--color-border)] px-3 py-3"
      >
        <template v-if="!readonly">
          <GameReviewStatusSelector
            :model-value="season.status ?? UserTitleStatus.PLANNED"
            :statuses="seasonStatuses"
            @update:model-value="updateSeasonStatus(season, $event)"
          />

          <div v-if="(season.status ?? UserTitleStatus.PLANNED) !== UserTitleStatus.PLANNED">
            <GameReviewRating
              :model-value="season.score || 0"
              @update:model-value="updateSeasonScore(season, $event)"
            />
            <button
              v-if="season.score_is_manual && season.avg_score != null"
              type="button"
              class="mt-1 text-xs text-primary-500 hover:underline"
              :disabled="savingKey === `season-reset-${season.season_number}`"
              @click="resetSeasonScore(season)"
            >
              Сбросить к средней ({{ season.avg_score }})
            </button>
          </div>

          <GameReviewTextArea
            :model-value="localSeasonReviews[season.season_number] ?? ''"
            @update:model-value="updateSeasonReview(season, $event)"
          />
        </template>

        <template v-else>
          <div class="text-xs text-[var(--color-text-muted)] space-y-1">
            <div v-if="season.status">Статус: {{ seasonStatuses.find(s => s.id === season.status)?.label }}</div>
            <div v-if="season.score != null">Оценка: {{ season.score }}/10</div>
            <div v-if="season.review_text" class="whitespace-pre-wrap text-[var(--color-text)]">{{ season.review_text }}</div>
          </div>
        </template>

        <div v-if="loadingEpisodes.has(season.season_number)" class="text-xs text-[var(--color-text-muted)]">
          Загрузка серий…
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="episode in season.episodes"
            :key="episode.title_episode_id"
            class="rounded-md border border-[var(--color-border)]/70 px-2.5 py-2"
          >
            <div class="mb-2 text-sm text-[var(--color-text)]">
              {{ episodeLabel(episode.episode_number, episode.name) }}
              <span v-if="episode.score != null" class="ml-1 text-xs text-[var(--color-text-muted)]">
                {{ episode.score }}/10
              </span>
            </div>

            <template v-if="!readonly">
              <GameReviewStatusSelector
                :model-value="episode.status ?? UserTitleStatus.PLANNED"
                :statuses="episodeStatuses"
                @update:model-value="updateEpisodeStatus(season, episode.episode_number, $event)"
              />
              <GameReviewRating
                v-if="(episode.status ?? UserTitleStatus.PLANNED) !== UserTitleStatus.PLANNED"
                :model-value="episode.score || 0"
                @update:model-value="updateEpisodeScore(season, episode.episode_number, $event)"
              />
            </template>
          </div>

          <div
            v-if="season.episodes_loaded && season.episodes.length === 0"
            class="text-xs text-[var(--color-text-muted)]"
          >
            Серии не найдены
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
