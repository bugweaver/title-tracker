<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue';
import {
  UserTitleStatus,
  type SeasonStructure,
  type SeriesStructure,
} from '@/entities/title';
import { titlesApi } from '@/shared/api/titles';
import GameReviewRating from './GameReviewRating.vue';
import GameReviewStatusSelector from './GameReviewStatusSelector.vue';
import GameReviewTextArea from './GameReviewTextArea.vue';

const EPISODE_PAGE_SIZE = 20;

const props = defineProps<{
  userTitleId: number;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  (e: 'updated', structure: SeriesStructure): void;
}>();

const structure = ref<SeriesStructure | null>(null);
const isLoading = ref(false);
const loadError = ref(false);
const expandedSeasons = ref<Set<number>>(new Set());
const loadingEpisodes = ref<Set<number>>(new Set());
const savingKey = ref<string | null>(null);
const localSeasonReviews = ref<Record<number, string>>({});
/** season_number → 1-based page of episodes */
const episodePageBySeason = ref<Record<number, number>>({});
/** season_number → jump input draft */
const jumpDraftBySeason = ref<Record<number, string>>({});
const highlightedEpisode = ref<{ season: number; episode: number } | null>(null);
const debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();

const isSingleSeason = computed(() => (structure.value?.seasons.length ?? 0) === 1);
const sectionTitle = computed(() =>
  isSingleSeason.value ? 'Серии' : 'Сезоны и серии',
);

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

const ensureSeasonExpanded = async (season: SeasonStructure) => {
  const number = season.season_number;
  if (!expandedSeasons.value.has(number)) {
    expandedSeasons.value.add(number);
    expandedSeasons.value = new Set(expandedSeasons.value);
  }

  if (season.episodes_loaded) return;

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
          s.season_number === number ? updatedSeason : s,
        ),
      };
    }
  } catch (error) {
    console.error('Failed to sync season episodes', error);
    expandedSeasons.value.delete(number);
    expandedSeasons.value = new Set(expandedSeasons.value);
  } finally {
    loadingEpisodes.value.delete(number);
    loadingEpisodes.value = new Set(loadingEpisodes.value);
  }
};

const loadStructure = async () => {
  if (!props.userTitleId) return;
  isLoading.value = true;
  loadError.value = false;
  try {
    const data = props.readonly
      ? await titlesApi.getPublicStructure(props.userTitleId)
      : await titlesApi.getStructure(props.userTitleId);
    structure.value = data;
    syncLocalReviews(data);
    // Single synthetic season (anime): open episodes immediately
    if (data.seasons.length === 1) {
      await ensureSeasonExpanded(data.seasons[0]);
    }
  } catch (error) {
    console.error('Failed to load series structure', error);
    structure.value = null;
    loadError.value = true;
  } finally {
    isLoading.value = false;
  }
};

watch(
  () => props.userTitleId,
  () => {
    expandedSeasons.value = new Set();
    episodePageBySeason.value = {};
    jumpDraftBySeason.value = {};
    highlightedEpisode.value = null;
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
  await ensureSeasonExpanded(season);
};

const episodePageCount = (season: SeasonStructure) =>
  Math.max(1, Math.ceil(season.episodes.length / EPISODE_PAGE_SIZE));

const currentEpisodePage = (season: SeasonStructure) => {
  const page = episodePageBySeason.value[season.season_number] ?? 1;
  return Math.min(Math.max(1, page), episodePageCount(season));
};

const visibleEpisodes = (season: SeasonStructure) => {
  const page = currentEpisodePage(season);
  const start = (page - 1) * EPISODE_PAGE_SIZE;
  return season.episodes.slice(start, start + EPISODE_PAGE_SIZE);
};

const episodeRangeLabel = (season: SeasonStructure) => {
  if (season.episodes.length === 0) return '';
  const page = currentEpisodePage(season);
  const start = (page - 1) * EPISODE_PAGE_SIZE + 1;
  const end = Math.min(page * EPISODE_PAGE_SIZE, season.episodes.length);
  return `${start}–${end} из ${season.episodes.length}`;
};

const setEpisodePage = (season: SeasonStructure, page: number) => {
  const clamped = Math.min(Math.max(1, page), episodePageCount(season));
  episodePageBySeason.value = {
    ...episodePageBySeason.value,
    [season.season_number]: clamped,
  };
};

const setJumpDraft = (seasonNumber: number, value: string) => {
  jumpDraftBySeason.value = {
    ...jumpDraftBySeason.value,
    [seasonNumber]: value,
  };
};

const episodeDomId = (seasonNumber: number, episodeNumber: number) =>
  `episode-${props.userTitleId}-${seasonNumber}-${episodeNumber}`;

const scrollToEpisode = async (seasonNumber: number, episodeNumber: number) => {
  await nextTick();
  // Wait for page swap / highlight paint inside the modal scroller
  requestAnimationFrame(() => {
    const el = document.getElementById(episodeDomId(seasonNumber, episodeNumber));
    el?.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
  });
};

const jumpToEpisode = async (season: SeasonStructure) => {
  const raw = jumpDraftBySeason.value[season.season_number]?.trim();
  if (!raw) return;
  const episodeNumber = Number.parseInt(raw, 10);
  if (!Number.isFinite(episodeNumber) || episodeNumber < 1) return;

  const max = season.episodes.length || season.episode_count || 0;
  if (max > 0 && episodeNumber > max) return;

  const page = Math.ceil(episodeNumber / EPISODE_PAGE_SIZE);
  setEpisodePage(season, page);
  highlightedEpisode.value = {
    season: season.season_number,
    episode: episodeNumber,
  };
  await scrollToEpisode(season.season_number, episodeNumber);
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

const seasonLabel = (season: SeasonStructure) => {
  const named = season.name?.trim();
  if (named && !/^сезон\s*1$/i.test(named)) return named;
  if (isSingleSeason.value) return 'Серии';
  return named || `Сезон ${season.season_number}`;
};

const episodeLabel = (episodeNumber: number, name: string | null) => {
  const trimmed = name?.trim();
  if (!trimmed) return `Эпизод ${episodeNumber}`;
  // Avoid "Эпизод 1: Серия 1" when the provider name is just a number label
  const redundant = new RegExp(`^(серия|эпизод)\\s*0*${episodeNumber}$`, 'i');
  if (redundant.test(trimmed)) return `Эпизод ${episodeNumber}`;
  return `Эпизод ${episodeNumber}: ${trimmed}`;
};

const isEpisodeHighlighted = (seasonNumber: number, episodeNumber: number) =>
  highlightedEpisode.value?.season === seasonNumber
  && highlightedEpisode.value?.episode === episodeNumber;
</script>

<template>
  <div class="space-y-3">
    <div
      v-if="!isSingleSeason || isLoading"
      class="flex items-center justify-between gap-2"
    >
      <h3
        v-if="!isSingleSeason"
        class="text-sm font-medium text-[var(--color-text-secondary)]"
      >
        {{ sectionTitle }}
      </h3>
      <span v-if="isLoading" class="text-xs text-[var(--color-text-muted)]">Загрузка…</span>
    </div>

    <div v-if="!isLoading && loadError" class="text-sm text-[var(--color-text-muted)]">
      Не удалось загрузить {{ isSingleSeason ? 'серии' : 'сезоны' }}.
      <button type="button" class="ml-1 text-primary-500 hover:underline" @click="loadStructure">
        Повторить
      </button>
    </div>

    <div v-else-if="!isLoading && structure && structure.seasons.length === 0" class="text-sm text-[var(--color-text-muted)]">
      Серии пока не найдены
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

          <div>
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

        <div v-else class="flex flex-col gap-5">
          <div
            v-if="season.episodes.length > EPISODE_PAGE_SIZE"
            class="flex flex-col gap-2 rounded-md border border-[var(--color-border)]/60 px-3 py-2"
          >
            <div class="flex items-center justify-between gap-2">
              <button
                type="button"
                class="rounded px-2 py-1 text-xs text-[var(--color-text-secondary)] hover:bg-[var(--color-background)] disabled:opacity-40"
                :disabled="currentEpisodePage(season) <= 1"
                @click="setEpisodePage(season, currentEpisodePage(season) - 1)"
              >
                ← Назад
              </button>
              <span class="text-xs text-[var(--color-text-muted)]">
                {{ episodeRangeLabel(season) }}
              </span>
              <button
                type="button"
                class="rounded px-2 py-1 text-xs text-[var(--color-text-secondary)] hover:bg-[var(--color-background)] disabled:opacity-40"
                :disabled="currentEpisodePage(season) >= episodePageCount(season)"
                @click="setEpisodePage(season, currentEpisodePage(season) + 1)"
              >
                Дальше →
              </button>
            </div>
            <form
              class="flex items-center gap-2"
              @submit.prevent="jumpToEpisode(season)"
            >
              <label
                class="shrink-0 text-xs text-[var(--color-text-muted)]"
                :for="`jump-ep-${season.season_number}`"
              >
                К серии
              </label>
              <input
                :id="`jump-ep-${season.season_number}`"
                :value="jumpDraftBySeason[season.season_number] ?? ''"
                type="number"
                min="1"
                :max="season.episodes.length || season.episode_count || undefined"
                inputmode="numeric"
                placeholder="№"
                class="w-20 rounded-md border border-[var(--color-border)] bg-[var(--color-background)] px-2 py-1 text-sm text-[var(--color-text)] outline-none focus:border-primary-500"
                @input="setJumpDraft(season.season_number, ($event.target as HTMLInputElement).value)"
              >
              <button
                type="submit"
                class="rounded-md px-2 py-1 text-xs text-primary-500 hover:underline"
              >
                Перейти
              </button>
            </form>
          </div>

          <div
            v-for="episode in visibleEpisodes(season)"
            :id="episodeDomId(season.season_number, episode.episode_number)"
            :key="episode.title_episode_id"
            class="flex flex-col gap-4 rounded-md border px-3 py-3"
            :class="isEpisodeHighlighted(season.season_number, episode.episode_number)
              ? 'border-primary-500 bg-primary-500/5'
              : 'border-[var(--color-border)]/70'"
          >
            <div class="text-sm text-[var(--color-text)]">
              {{ episodeLabel(episode.episode_number, episode.name) }}
              <span v-if="episode.score != null" class="ml-1 text-xs text-[var(--color-text-muted)]">
                {{ episode.score }}/10
              </span>
            </div>

            <div v-if="!readonly" class="flex flex-col gap-3">
              <GameReviewStatusSelector
                compact
                :model-value="episode.status ?? UserTitleStatus.PLANNED"
                :statuses="episodeStatuses"
                @update:model-value="updateEpisodeStatus(season, episode.episode_number, $event)"
              />
              <GameReviewRating
                :model-value="episode.score || 0"
                @update:model-value="updateEpisodeScore(season, episode.episode_number, $event)"
              />
            </div>
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
