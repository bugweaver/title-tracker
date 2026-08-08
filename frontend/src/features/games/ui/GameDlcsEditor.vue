<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue';
import {
  UserTitleStatus,
  type DlcItem,
  type GameDlcs,
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
  (e: 'updated', dlcs: GameDlcs): void;
}>();

const structure = ref<GameDlcs | null>(null);
const isLoading = ref(false);
const expandedDlcs = ref<Set<number>>(new Set());
const savingKey = ref<string | null>(null);
const localReviews = ref<Record<number, string>>({});
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

const dlcStatuses = [
  { id: UserTitleStatus.COMPLETED, label: 'Прошел' },
  { id: UserTitleStatus.PLAYING, label: 'Играю' },
  { id: UserTitleStatus.DROPPED, label: 'Дропнул' },
  { id: UserTitleStatus.PLANNED, label: 'В планах' },
  { id: UserTitleStatus.ON_HOLD, label: 'На паузе' },
];

const statusLabel = (status: UserTitleStatus | null) =>
  dlcStatuses.find((s) => s.id === status)?.label ?? 'Не добавлено';

const syncLocalReviews = (next: GameDlcs) => {
  const reviews: Record<number, string> = {};
  for (const dlc of next.dlcs) {
    reviews[dlc.title_id] = dlc.review_text || '';
  }
  localReviews.value = reviews;
};

const applyStructure = (next: GameDlcs) => {
  structure.value = next;
  syncLocalReviews(next);
  emit('updated', next);
};

const loadDlcs = async () => {
  if (!props.userTitleId) return;
  isLoading.value = true;
  try {
    const data = props.readonly
      ? await titlesApi.getPublicDlcs(props.userTitleId)
      : await titlesApi.getDlcs(props.userTitleId);
    structure.value = data;
    syncLocalReviews(data);
  } catch (error) {
    console.error('Failed to load game DLCs', error);
  } finally {
    isLoading.value = false;
  }
};

watch(
  () => props.userTitleId,
  () => {
    expandedDlcs.value = new Set();
    void loadDlcs();
  },
  { immediate: true },
);

const toggleDlc = (dlc: DlcItem) => {
  if (expandedDlcs.value.has(dlc.title_id)) {
    expandedDlcs.value.delete(dlc.title_id);
  } else {
    expandedDlcs.value.add(dlc.title_id);
  }
  expandedDlcs.value = new Set(expandedDlcs.value);
};

const updateDlcScore = (dlc: DlcItem, score: number) => {
  if (props.readonly) return;
  if (structure.value) {
    structure.value = {
      ...structure.value,
      dlcs: structure.value.dlcs.map((item) =>
        item.title_id === dlc.title_id
          ? { ...item, score: score || null, status: item.status ?? UserTitleStatus.PLAYING }
          : item,
      ),
    };
  }
  debounce(`dlc-score-${dlc.title_id}`, async () => {
    savingKey.value = `dlc-score-${dlc.title_id}`;
    try {
      const next = await titlesApi.updateDlc(props.userTitleId, dlc.title_id, {
        score: score || undefined,
        clear_score: !score,
        status: dlc.status ?? UserTitleStatus.PLAYING,
      });
      applyStructure(next);
    } catch (error) {
      console.error('Failed to update DLC score', error);
    } finally {
      savingKey.value = null;
    }
  });
};

const updateDlcStatus = async (dlc: DlcItem, status: UserTitleStatus) => {
  if (props.readonly) return;
  savingKey.value = `dlc-status-${dlc.title_id}`;
  try {
    const next = await titlesApi.updateDlc(props.userTitleId, dlc.title_id, {
      status,
      score: dlc.score ?? undefined,
    });
    applyStructure(next);
  } catch (error) {
    console.error('Failed to update DLC status', error);
  } finally {
    savingKey.value = null;
  }
};

const updateDlcReview = (dlc: DlcItem, reviewText: string) => {
  if (props.readonly) return;
  localReviews.value = {
    ...localReviews.value,
    [dlc.title_id]: reviewText,
  };
  debounce(`dlc-review-${dlc.title_id}`, async () => {
    savingKey.value = `dlc-review-${dlc.title_id}`;
    try {
      const next = await titlesApi.updateDlc(props.userTitleId, dlc.title_id, {
        review_text: reviewText,
        is_spoiler: /<[^<>]+>/.test(reviewText),
        status: dlc.status ?? UserTitleStatus.PLAYING,
        score: dlc.score ?? undefined,
      });
      applyStructure(next);
    } catch (error) {
      console.error('Failed to update DLC review', error);
    } finally {
      savingKey.value = null;
    }
  }, 700);
};

const clearDlcTracking = async (dlc: DlcItem) => {
  if (props.readonly || !dlc.user_title_id) return;
  savingKey.value = `dlc-clear-${dlc.title_id}`;
  try {
    await titlesApi.deleteDlcTracking(props.userTitleId, dlc.title_id);
    await loadDlcs();
    if (structure.value) emit('updated', structure.value);
  } catch (error) {
    console.error('Failed to clear DLC tracking', error);
  } finally {
    savingKey.value = null;
  }
};
</script>

<template>
  <div
    v-if="!(readonly && !isLoading && (!structure || structure.dlcs.length === 0))"
    class="space-y-3"
  >
    <div class="flex items-center justify-between gap-2">
      <h3 class="text-sm font-medium text-[var(--color-text-secondary)]">DLC и дополнения</h3>
      <span v-if="isLoading" class="text-xs text-[var(--color-text-muted)]">Загрузка…</span>
    </div>

    <div
      v-if="!isLoading && structure && structure.dlcs.length === 0"
      class="text-sm text-[var(--color-text-muted)]"
    >
      DLC не найдены
    </div>

    <div
      v-for="dlc in structure?.dlcs ?? []"
      :key="dlc.title_id"
      class="rounded-lg border border-[var(--color-border)] bg-[var(--color-background-soft)]/40"
    >
      <button
        type="button"
        class="flex w-full items-center justify-between gap-3 px-3 py-3 text-left"
        @click="toggleDlc(dlc)"
      >
        <div class="flex min-w-0 items-center gap-3">
          <img
            v-if="dlc.cover_image"
            :src="dlc.cover_image"
            :alt="dlc.name"
            class="h-12 w-9 shrink-0 rounded object-cover"
          />
          <div class="min-w-0">
            <div class="truncate text-sm font-medium text-[var(--color-text)]">
              {{ dlc.name }}
            </div>
            <div class="mt-0.5 text-xs text-[var(--color-text-muted)]">
              <span v-if="dlc.release_year">{{ dlc.release_year }} · </span>
              <span>{{ statusLabel(dlc.status) }}</span>
              <span v-if="dlc.score != null"> · {{ dlc.score }}/10</span>
            </div>
          </div>
        </div>
        <span class="shrink-0 text-[var(--color-text-muted)]">
          {{ expandedDlcs.has(dlc.title_id) ? '▾' : '▸' }}
        </span>
      </button>

      <div
        v-if="expandedDlcs.has(dlc.title_id)"
        class="space-y-4 border-t border-[var(--color-border)] px-3 py-3"
      >
        <template v-if="!readonly">
          <GameReviewStatusSelector
            :model-value="dlc.status ?? UserTitleStatus.PLANNED"
            :statuses="dlcStatuses"
            @update:model-value="updateDlcStatus(dlc, $event)"
          />

          <div v-if="(dlc.status ?? UserTitleStatus.PLANNED) !== UserTitleStatus.PLANNED">
            <GameReviewRating
              :model-value="dlc.score || 0"
              @update:model-value="updateDlcScore(dlc, $event)"
            />
          </div>

          <GameReviewTextArea
            :model-value="localReviews[dlc.title_id] ?? ''"
            @update:model-value="updateDlcReview(dlc, $event)"
          />

          <button
            v-if="dlc.user_title_id"
            type="button"
            class="text-xs text-[var(--color-text-muted)] hover:text-red-500 hover:underline disabled:opacity-50"
            :disabled="savingKey === `dlc-clear-${dlc.title_id}`"
            @click="clearDlcTracking(dlc)"
          >
            Убрать из списка
          </button>
        </template>

        <template v-else>
          <div class="space-y-1 text-xs text-[var(--color-text-muted)]">
            <div>Статус: {{ statusLabel(dlc.status) }}</div>
            <div v-if="dlc.score != null">Оценка: {{ dlc.score }}/10</div>
            <div
              v-if="dlc.review_text"
              class="whitespace-pre-wrap text-[var(--color-text)]"
            >{{ dlc.review_text }}</div>
            <div v-else-if="!dlc.status">DLC не добавлено в список</div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
