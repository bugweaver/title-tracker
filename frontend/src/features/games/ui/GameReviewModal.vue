<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import AppButton from '@/shared/ui/AppButton.vue';
import AppSelect from '@/shared/ui/AppSelect.vue';
import { type TitleSearchResult, titlesApi, type Screenshot } from '@/shared/api/titles';
import { UserTitleStatus } from '@/entities/title';

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

// Screenshots
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
      // Reset
      status.value = UserTitleStatus.COMPLETED;
      rating.value = 0;
      review.value = '';
      existingScreenshots.value = [];
      const now = new Date();
      selectedYear.value = now.getFullYear();
      selectedMonth.value = now.getMonth();
    }
    // Always reset pending state
    pendingFiles.value = [];
    pendingPreviews.value = [];
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

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const insertSpoiler = () => {
  if (!textareaRef.value) return;
  
  const el = textareaRef.value;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  const text = review.value;
  
  const before = text.substring(0, start);
  const selection = text.substring(start, end);
  const after = text.substring(end);
  
  review.value = before + '<' + (selection || 'спойлер') + '>' + after;
  
  setTimeout(() => {
    el.focus();
    const newCursorPos = start + 1 + (selection.length || 7) + 1;
    el.setSelectionRange(newCursorPos, newCursorPos);
  }, 0);
};

// Screenshot handlers
const fileInputRef = ref<HTMLInputElement | null>(null);

const openFileDialog = () => {
  fileInputRef.value?.click();
};

const onFileSelected = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files) return;
  
  const files = Array.from(input.files);
  const availableSlots = MAX_SCREENSHOTS - totalScreenshots.value;
  const filesToAdd = files.slice(0, availableSlots);
  
  for (const file of filesToAdd) {
    if (file.size > 5 * 1024 * 1024) continue; // Skip > 5MB
    if (!file.type.startsWith('image/')) continue;
    
    pendingFiles.value.push(file);
    pendingPreviews.value.push(URL.createObjectURL(file));
  }
  
  // Reset input
  input.value = '';
};

const onDrop = (event: DragEvent) => {
  event.preventDefault();
  isDragging.value = false;
  
  if (!event.dataTransfer?.files) return;
  
  const files = Array.from(event.dataTransfer.files);
  const availableSlots = MAX_SCREENSHOTS - totalScreenshots.value;
  const filesToAdd = files.slice(0, availableSlots);
  
  for (const file of filesToAdd) {
    if (file.size > 5 * 1024 * 1024) continue;
    if (!file.type.startsWith('image/')) continue;
    
    pendingFiles.value.push(file);
    pendingPreviews.value.push(URL.createObjectURL(file));
  }
};

const isDragging = ref(false);

const onDragOver = (event: DragEvent) => {
  event.preventDefault();
  isDragging.value = true;
};

const onDragLeave = () => {
  isDragging.value = false;
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

// Lightbox for preview
const previewLightboxOpen = ref(false);
const previewLightboxIndex = ref(0);

const allPreviewUrls = computed(() => {
  const existing = existingScreenshots.value
    .filter(s => !deletedScreenshotIds.value.includes(s.id))
    .map(s => s.url);
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
    // 1. Add/update the title entry
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

      // 2. Delete removed screenshots
      for (const id of deletedScreenshotIds.value) {
        try {
          await titlesApi.deleteScreenshot(id);
        } catch (err) {
          console.error('Failed to delete screenshot:', err);
        }
      }

      // 3. Upload new screenshots
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
</script>

<template>
  <div v-if="isOpen && title" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm" @click="$emit('close')">
    <div class="w-full max-w-lg bg-zinc-900 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]" @click.stop>
      
      <!-- Header -->
      <div class="p-6 flex gap-6 bg-zinc-800/50 items-start">
        <div class="w-24 h-36 bg-zinc-800 rounded-lg shadow-md flex-shrink-0 overflow-hidden">
          <img v-if="title.poster_url" :src="title.poster_url" class="w-full h-full object-cover" />
          <div v-else class="w-full h-full flex items-center justify-center text-zinc-600 text-xs">No Img</div>
        </div>
        
        <div class="flex-1">
          <div class="flex justify-between items-start mb-2">
            <h2 class="text-xl font-bold text-white leading-tight">{{ title.title }}</h2>
            <div v-if="status !== UserTitleStatus.PLANNED" class="flex flex-col items-center ml-2">
              <span class="text-3xl font-black text-primary-500 min-w-[3rem] text-center">{{ rating === 0 ? '-' : (rating === 10 ? '10' : rating.toFixed(1)) }}</span>
              <span class="text-2xl">{{ emoji }}</span>
            </div>
          </div>
          <p class="text-zinc-400 text-sm">
             {{ title.release_year }} 
             <span v-if="title.genres && title.genres.length">• {{ title.genres.join(', ') }}</span>
          </p>
        </div>
      </div>

      <div class="p-6 space-y-8 overflow-y-auto custom-scrollbar">
        
        <!-- Score Slider -->
        <div v-if="status !== UserTitleStatus.PLANNED" class="space-y-2 pb-2">
          <label class="text-sm font-medium text-zinc-400">Оценка</label>
          <input 
            type="range" 
            v-model.number="rating" 
            min="1" 
            max="10" 
            step="0.1"
            class="w-full h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-primary-500"
          />
          <div class="flex justify-between text-xs text-zinc-500 px-1">
            <span>1.0</span>
            <span>5.0</span>
            <span>10.0</span>
          </div>
        </div>

        <!-- Status -->
        <div class="space-y-4 pb-5">
          <div class="flex flex-wrap gap-2 ">
            <button 
              v-for="s in statuses" 
              :key="s.id"
              class="px-3 py-1.5 rounded-full text-sm font-medium transition-all border"
              :class="status === s.id 
                ? 'bg-primary-600 text-white border-primary-600' 
                : 'bg-transparent text-zinc-400 border-zinc-700 hover:border-zinc-500 '"
              @click="status = s.id"
            >
              {{ s.label }}
            </button>
          </div>
        </div>

        <!-- Date Input -->
        <div v-if="status === UserTitleStatus.COMPLETED" class="space-y-2 pb-2">
           <label class="text-sm font-medium text-zinc-400">Дата завершения</label>
           <div class="flex gap-2">
             <div class="w-1/2">
               <AppSelect
                 v-model="selectedMonth"
                 :options="monthOptions"
                 placeholder="Месяц"
               />
             </div>
             <div class="w-1/2">
               <AppSelect
                 v-model="selectedYear"
                 :options="yearOptions"
                 placeholder="Год"
               />
             </div>
           </div>
        </div>

        <!-- Review -->
        <div class="space-y-2">
          <textarea 
            v-model="review" 
            ref="textareaRef"
            class="w-full h-32 bg-zinc-800 rounded-lg p-3 text-white resize-none outline-none focus:ring-2 focus:ring-primary-500 placeholder-zinc-600"
            placeholder="Напишите ваше мнение..."
            maxlength="5000"
          ></textarea>
          <div class="flex justify-between pl-2 items-center">
            <span class="text-xs text-zinc-500">{{ review.length }} / 5000</span>
            
            <button 
              type="button"
              @click="insertSpoiler"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors text-zinc-400 hover:text-white hover:bg-zinc-700"
              title="Обернуть выделенный текст в спойлер"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
              Спойлер
            </button>
          </div>
        </div>

        <!-- Screenshots -->
        <div class="space-y-3">
          <label class="text-sm font-medium text-zinc-400 block" style="margin-bottom: 12px;">
            Скриншоты 
            <span class="text-zinc-600">({{ totalScreenshots }}/{{ MAX_SCREENSHOTS }})</span>
          </label>

          <!-- Existing screenshots -->
          <div v-if="existingScreenshots.length > 0" class="grid grid-cols-3 gap-2">
            <div 
              v-for="screenshot in existingScreenshots" 
              :key="screenshot.id"
              class="relative group rounded-lg overflow-hidden aspect-video bg-zinc-800"
              :class="{ 'opacity-30': deletedScreenshotIds.includes(screenshot.id) }"
            >
              <img 
                :src="screenshot.url" 
                class="w-full h-full object-cover cursor-pointer" 
                @click="!deletedScreenshotIds.includes(screenshot.id) && openPreviewLightbox(screenshot.url)"
              />
              <!-- Magnify icon -->
              <div 
                v-if="!deletedScreenshotIds.includes(screenshot.id)" 
                class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  <line x1="11" y1="8" x2="11" y2="14"></line>
                  <line x1="8" y1="11" x2="14" y2="11"></line>
                </svg>
              </div>
              <button
                v-if="!deletedScreenshotIds.includes(screenshot.id)"
                @click.stop="markExistingForDeletion(screenshot)"
                class="absolute top-1 right-1 w-6 h-6 bg-red-600 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-white text-xs z-10"
                title="Удалить"
              >✕</button>
              <div
                v-else
                class="absolute inset-0 flex items-center justify-center bg-black/50 text-zinc-300 text-xs"
              >Удалён</div>
            </div>
          </div>

          <!-- Pending screenshots previews -->
          <div v-if="pendingPreviews.length > 0" class="grid grid-cols-3 gap-2">
            <div 
              v-for="(preview, index) in pendingPreviews" 
              :key="'pending-' + index"
              class="relative group rounded-lg overflow-hidden aspect-video bg-zinc-800"
            >
              <img 
                :src="preview" 
                class="w-full h-full object-cover cursor-pointer" 
                @click="openPreviewLightbox(preview)"
              />
              <!-- Magnify icon -->
              <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  <line x1="11" y1="8" x2="11" y2="14"></line>
                  <line x1="8" y1="11" x2="14" y2="11"></line>
                </svg>
              </div>
              <button
                @click.stop="removePendingFile(index)"
                class="absolute top-1 right-1 w-6 h-6 bg-red-600 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-white text-xs z-10"
                title="Убрать"
              >✕</button>
              <div class="absolute bottom-1 left-1 px-1.5 py-0.5 bg-primary-600/80 rounded text-[10px] text-white">Новый</div>
            </div>
          </div>

          <!-- Drop zone -->
          <div
            v-if="canAddMore"
            class="border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors !mt-6"
            :class="isDragging 
              ? 'border-primary-500 bg-primary-500/10' 
              : 'border-zinc-700 hover:border-zinc-500'"
            @click="openFileDialog"
            @drop="onDrop"
            @dragover="onDragOver"
            @dragleave="onDragLeave"
          >
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              multiple
              class="hidden"
              @change="onFileSelected"
            />
            <div class="flex flex-col items-center gap-1.5">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-zinc-500">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
              <span class="text-xs text-zinc-500">
                Перетащите или нажмите для загрузки
              </span>
              <span class="text-[10px] text-zinc-600">JPEG, PNG, WebP, GIF • до 5 МБ</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-zinc-800 flex justify-end gap-3 bg-zinc-900">
        <AppButton variant="ghost" @click="$emit('close')">Отмена</AppButton>
        <AppButton :loading="isSubmitting || isUploadingScreenshots" @click="handleSubmit">
          {{ isUploadingScreenshots ? 'Загрузка...' : 'Добавить' }}
        </AppButton>
      </div>
    
    </div>
  </div>

  <!-- Preview Lightbox -->
  <Teleport to="body">
    <div 
      v-if="previewLightboxOpen && allPreviewUrls.length > 0" 
      class="fixed inset-0 z-[200] bg-black/95 flex items-center justify-center"
      @click="closePreviewLightbox"
    >
      <button 
        class="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/10 hover:bg-white/25 border-none text-white text-xl cursor-pointer flex items-center justify-center transition-colors z-[201]"
        @click.stop="closePreviewLightbox"
      >✕</button>
      <button 
        v-if="previewLightboxIndex > 0" 
        class="absolute left-5 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/25 border-none text-white text-4xl cursor-pointer flex items-center justify-center transition-colors z-[201]"
        @click.stop="previewLightboxIndex--"
      >‹</button>
      <div class="flex flex-col items-center gap-3 max-w-[90vw] max-h-[90vh]" @click.stop>
        <img 
          :src="allPreviewUrls[previewLightboxIndex]" 
          class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
        />
        <span class="text-white/60 text-sm">{{ previewLightboxIndex + 1 }} / {{ allPreviewUrls.length }}</span>
      </div>
      <button 
        v-if="previewLightboxIndex < allPreviewUrls.length - 1" 
        class="absolute right-5 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/25 border-none text-white text-4xl cursor-pointer flex items-center justify-center transition-colors z-[201]"
        @click.stop="previewLightboxIndex++"
      >›</button>
    </div>
  </Teleport>
</template>

<style scoped>
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
