<script setup lang="ts">
import { ref, computed, watch, type CSSProperties } from 'vue';
import { type TitleSearchResult, titlesApi, type Screenshot } from '@/shared/api/titles';
import { UserTitleStatus, useTitleStore } from '@/entities/title';
import GameReviewCompletionDate from './GameReviewCompletionDate.vue';
import GameReviewFooter from './GameReviewFooter.vue';
import GameReviewHeader from './GameReviewHeader.vue';
import GameReviewRating from './GameReviewRating.vue';
import GameReviewScreenshots from './GameReviewScreenshots.vue';
import GameReviewStatusSelector from './GameReviewStatusSelector.vue';
import GameReviewTextArea from './GameReviewTextArea.vue';
import ImageLightbox from './ImageLightbox.vue';

const titleStore = useTitleStore();

const props = defineProps<{
  isOpen: boolean;
  title: TitleSearchResult | null;
  initialData?: {
    userTitleId?: number;
    status: UserTitleStatus;
    score: number | null;
    review_text: string | null;
    is_spoiler?: boolean;
    finished_at?: string | null;
    screenshots?: Screenshot[];
  } | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'added'): void;
}>();

const rating = ref(0);
const status = ref<UserTitleStatus>(UserTitleStatus.COMPLETED);
const review = ref('');
const selectedYear = ref<number | null>(null);
const selectedMonth = ref<number | null>(null);
const isSubmitting = ref(false);
const isDeleting = ref(false);
const showDeleteConfirm = ref(false);

const pendingFiles = ref<File[]>([]);
const pendingPreviews = ref<string[]>([]);
const existingScreenshots = ref<Screenshot[]>([]);
const deletedScreenshotIds = ref<number[]>([]);
const isUploadingScreenshots = ref(false);
const MAX_SCREENSHOTS = 10;

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    if (props.initialData) {
      status.value = props.initialData.status;
      rating.value = props.initialData.score || 0;
      review.value = props.initialData.review_text || '';
      existingScreenshots.value = props.initialData.screenshots ? [...props.initialData.screenshots] : [];
      if (props.initialData.finished_at) {
        const date = new Date(props.initialData.finished_at);
        selectedYear.value = date.getFullYear();
        selectedMonth.value = date.getMonth();
      } else {
        selectedYear.value = null;
        selectedMonth.value = null;
      }
    } else {
      status.value = UserTitleStatus.COMPLETED;
      rating.value = 0;
      review.value = '';
      existingScreenshots.value = [];
      const now = new Date();
      selectedYear.value = now.getFullYear();
      selectedMonth.value = now.getMonth();
    }

    pendingFiles.value = [];
    pendingPreviews.value = [];
    showDeleteConfirm.value = false;
    deletedScreenshotIds.value = [];
  }
});

const totalScreenshots = computed(() =>
  existingScreenshots.value.length - deletedScreenshotIds.value.length + pendingFiles.value.length
);

const canAddMore = computed(() => totalScreenshots.value < MAX_SCREENSHOTS);

const statuses = computed(() => {
  const isGame = props.title?.type === 'game';
  const isMovie = props.title?.type === 'movie';

  return [
    { id: UserTitleStatus.COMPLETED, label: isGame ? 'Прошел' : 'Посмотрел' },
    ...(!isMovie ? [{ id: isGame ? UserTitleStatus.PLAYING : UserTitleStatus.WATCHING, label: isGame ? 'Играю' : 'Смотрю' }] : []),
    { id: UserTitleStatus.DROPPED, label: 'Дропнул' },
    { id: UserTitleStatus.PLANNED, label: 'В планах' },
    { id: UserTitleStatus.ON_HOLD, label: 'На паузе' },
  ];
});

const emoji = computed(() => {
  if (rating.value >= 9) return '🤩';
  if (rating.value >= 7.5) return '🙂';
  if (rating.value >= 5) return '😐';
  if (rating.value >= 3) return '😕';
  return '💩';
});

const interpolateColor = (
  from: [number, number, number],
  to: [number, number, number],
  amount: number,
): [number, number, number] => [
  Math.round(from[0] + (to[0] - from[0]) * amount),
  Math.round(from[1] + (to[1] - from[1]) * amount),
  Math.round(from[2] + (to[2] - from[2]) * amount),
];

const ratingToneRgb = computed(() => {
  if (status.value === UserTitleStatus.PLANNED || rating.value <= 0) {
    return [113, 113, 122];
  }

  const score = Math.min(10, Math.max(1, rating.value));

  if (score <= 5) {
    return interpolateColor([239, 68, 68], [245, 158, 11], (score - 1) / 4);
  }

  return interpolateColor([245, 158, 11], [16, 185, 129], (score - 5) / 5);
});

const reviewToneStyle = computed<CSSProperties>(() => ({
  '--review-tone-rgb': ratingToneRgb.value.join(' '),
} as CSSProperties));

const monthOptions = [
  { value: 0, label: 'Январь' },
  { value: 1, label: 'Февраль' },
  { value: 2, label: 'Март' },
  { value: 3, label: 'Апрель' },
  { value: 4, label: 'Май' },
  { value: 5, label: 'Июнь' },
  { value: 6, label: 'Июль' },
  { value: 7, label: 'Август' },
  { value: 8, label: 'Сентябрь' },
  { value: 9, label: 'Октябрь' },
  { value: 10, label: 'Ноябрь' },
  { value: 11, label: 'Декабрь' },
];

const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear();
  const startYear = 1980;
  const years = [];
  for (let y = currentYear; y >= startYear; y--) {
    years.push({ value: y, label: String(y) });
  }
  return years;
});

const addScreenshotFiles = (files: File[]) => {
  const availableSlots = MAX_SCREENSHOTS - totalScreenshots.value;
  const filesToAdd = files.slice(0, availableSlots);

  for (const file of filesToAdd) {
    if (file.size > 5 * 1024 * 1024) continue;
    if (!file.type.startsWith('image/')) continue;

    pendingFiles.value.push(file);
    pendingPreviews.value.push(URL.createObjectURL(file));
  }
};

const removePendingFile = (index: number) => {
  const url = pendingPreviews.value[index];
  if (url) URL.revokeObjectURL(url);
  pendingFiles.value.splice(index, 1);
  pendingPreviews.value.splice(index, 1);
};

const markExistingForDeletion = (screenshot: Screenshot) => {
  deletedScreenshotIds.value.push(screenshot.id);
};

const previewLightboxOpen = ref(false);
const previewLightboxIndex = ref(0);

const allPreviewUrls = computed(() => {
  const existing = existingScreenshots.value
    .filter(screenshot => !deletedScreenshotIds.value.includes(screenshot.id))
    .map(screenshot => screenshot.url);
  return [...existing, ...pendingPreviews.value];
});

const openPreviewLightbox = (url: string) => {
  const idx = allPreviewUrls.value.indexOf(url);
  previewLightboxIndex.value = idx >= 0 ? idx : 0;
  previewLightboxOpen.value = true;
};

const closePreviewLightbox = () => {
  previewLightboxOpen.value = false;
};

const handleSubmit = async () => {
  if (!props.title) return;

  isSubmitting.value = true;

  let finishedAtIso: string | undefined = undefined;
  if (status.value === UserTitleStatus.COMPLETED && selectedYear.value) {
    const year = selectedYear.value;
    const month = selectedMonth.value !== null ? selectedMonth.value : 0;
    const date = new Date(year, month, 1, 12, 0, 0);
    finishedAtIso = date.toISOString();
  }

  try {
    const result = await titlesApi.add({
      external_id: props.title.external_id,
      type: props.title.type,
      name: props.title.title,
      cover_url: props.title.poster_url,
      release_year: props.title.release_year,
      genres: props.title.genres || [],
      status: status.value,
      score: status.value === UserTitleStatus.PLANNED ? undefined : (rating.value || undefined),
      review_text: review.value || undefined,
      is_spoiler: /<[^<>]+>/.test(review.value),
      finished_at: finishedAtIso,
    });

    const userTitleId = result.id || props.initialData?.userTitleId;

    if (userTitleId) {
      isUploadingScreenshots.value = true;

      for (const id of deletedScreenshotIds.value) {
        try {
          await titlesApi.deleteScreenshot(id);
        } catch (err) {
          console.error('Failed to delete screenshot:', err);
        }
      }

      for (const file of pendingFiles.value) {
        try {
          await titlesApi.uploadScreenshot(userTitleId, file);
        } catch (err) {
          console.error('Failed to upload screenshot:', err);
        }
      }

      isUploadingScreenshots.value = false;
    }

    emit('added');
    emit('close');
  } catch (error) {
    console.error('Failed to add title:', error);
  } finally {
    isSubmitting.value = false;
    isUploadingScreenshots.value = false;
  }
};

const handleDelete = async () => {
  if (!props.initialData?.userTitleId) return;

  isDeleting.value = true;
  try {
    await titleStore.deleteTitle(props.initialData.userTitleId);
    emit('added');
    emit('close');
  } catch (error) {
    console.error('Failed to delete title:', error);
  } finally {
    isDeleting.value = false;
    showDeleteConfirm.value = false;
  }
};
</script>

<template>
  <div v-if="isOpen && title" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm" @click="$emit('close')">
    <div
      class="game-review-modal w-full max-w-lg rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
      :style="reviewToneStyle"
      @click.stop
    >
      <div class="game-review-modal-tint" aria-hidden="true"></div>

      <GameReviewHeader
        :title="title"
        :status="status"
        :rating="rating"
        :emoji="emoji"
      />

      <div class="p-6 space-y-8 overflow-y-auto custom-scrollbar">
        <GameReviewRating
          v-if="status !== UserTitleStatus.PLANNED"
          v-model="rating"
        />

        <GameReviewStatusSelector
          v-model="status"
          :statuses="statuses"
        />

        <GameReviewCompletionDate
          v-if="status === UserTitleStatus.COMPLETED"
          :month="selectedMonth"
          :year="selectedYear"
          :month-options="monthOptions"
          :year-options="yearOptions"
          @update:month="selectedMonth = $event"
          @update:year="selectedYear = $event"
        />

        <GameReviewTextArea v-model="review" />

        <GameReviewScreenshots
          :existing-screenshots="existingScreenshots"
          :deleted-screenshot-ids="deletedScreenshotIds"
          :pending-previews="pendingPreviews"
          :total-screenshots="totalScreenshots"
          :max-screenshots="MAX_SCREENSHOTS"
          :can-add-more="canAddMore"
          @add-files="addScreenshotFiles"
          @remove-pending="removePendingFile"
          @delete-existing="markExistingForDeletion"
          @open-preview="openPreviewLightbox"
        />
      </div>

      <GameReviewFooter
        v-model:show-delete-confirm="showDeleteConfirm"
        :has-user-title="Boolean(initialData?.userTitleId)"
        :is-deleting="isDeleting"
        :is-submitting="isSubmitting"
        :is-uploading-screenshots="isUploadingScreenshots"
        @close="$emit('close')"
        @submit="handleSubmit"
        @delete="handleDelete"
      />
    </div>
  </div>

  <ImageLightbox
    v-model:current-index="previewLightboxIndex"
    :is-open="previewLightboxOpen"
    :urls="allPreviewUrls"
    @close="closePreviewLightbox"
  />
</template>

<style scoped>
.game-review-modal {
  position: relative;
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid color-mix(in srgb, rgb(var(--review-tone-rgb)) 28%, var(--color-border));
  box-shadow:
    0 24px 70px rgb(0 0 0 / var(--review-modal-shadow)),
    0 0 0 1px rgb(var(--review-tone-rgb) / var(--review-modal-ring));
  transition:
    background-color 450ms ease,
    background 450ms ease,
    border-color 450ms ease,
    box-shadow 450ms ease,
    color 250ms ease;
}

.game-review-modal-tint {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-color: rgb(var(--review-tone-rgb));
  opacity: var(--review-modal-tint);
  transition: background-color 450ms ease, opacity 250ms ease;
}

.game-review-modal > :not(.game-review-modal-tint) {
  position: relative;
  z-index: 1;
}

:global(:root),
:global([data-theme="light"]) {
  --review-modal-tint: 0.08;
  --review-header-tint: 0.1;
  --review-footer-tint: 4%;
  --review-modal-ring: 0.16;
  --review-modal-shadow: 0.16;
}

:global([data-theme="dark"]) {
  --review-modal-tint: 0.13;
  --review-header-tint: 0.14;
  --review-footer-tint: 8%;
  --review-modal-ring: 0.22;
  --review-modal-shadow: 0.54;
}

:global([data-theme="midnight"]) {
  --review-modal-tint: 0.16;
  --review-header-tint: 0.18;
  --review-footer-tint: 10%;
  --review-modal-ring: 0.28;
  --review-modal-shadow: 0.5;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(113, 113, 122, 0.4);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(113, 113, 122, 0.6);
}
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(113, 113, 122, 0.4) transparent;
}
</style>
