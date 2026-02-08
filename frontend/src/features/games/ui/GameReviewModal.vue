<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import AppButton from '@/shared/ui/AppButton.vue';
import AppSelect from '@/shared/ui/AppSelect.vue';
import { type TitleSearchResult, titlesApi } from '@/shared/api/titles';
import { UserTitleStatus } from '@/entities/title';

const props = defineProps<{
  isOpen: boolean;
  title: TitleSearchResult | null;
  initialData?: {
    status: UserTitleStatus;
    score: number | null;
    review_text: string | null;
    finished_at?: string | null;
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

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    if (props.initialData) {
      status.value = props.initialData.status;
      rating.value = props.initialData.score || 0;
      review.value = props.initialData.review_text || '';
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
      const now = new Date();
      selectedYear.value = now.getFullYear();
      selectedMonth.value = now.getMonth();
    }
  }
});

const statuses = computed(() => {
  const isGame = props.title?.type === 'game';
  const isMovie = props.title?.type === 'movie';
  
  return [
    { id: UserTitleStatus.COMPLETED, label: isGame ? 'Прошел' : 'Посмотрел' },
    // Exclude Playing/Watching for movies
    ...(!isMovie ? [{ id: UserTitleStatus.PLAYING, label: isGame ? 'Играю' : 'Смотрю' }] : []),
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

const isSubmitDisabled = computed(() => {
  if (isSubmitting.value) return true;
  if (status.value === UserTitleStatus.PLANNED) return false;
  return rating.value === 0;
});

const handleSubmit = async () => {
  if (!props.title) return;
  
  isSubmitting.value = true;
  
  let finishedAtIso: string | undefined = undefined;
  if (status.value === UserTitleStatus.COMPLETED && selectedYear.value) {
     const year = selectedYear.value;
     const month = selectedMonth.value !== null ? selectedMonth.value : 0; // Default to Jan
     // Create date at noon to avoid timezone shifting to previous day
     const date = new Date(year, month, 1, 12, 0, 0); 
     finishedAtIso = date.toISOString();
  }

  try {
    await titlesApi.add({
      external_id: props.title.external_id,
      type: props.title.type,
      name: props.title.title,
      cover_url: props.title.poster_url,
      release_year: props.title.release_year,
      genres: props.title.genres || [],
      status: status.value,
      score: status.value === UserTitleStatus.PLANNED ? undefined : (rating.value || undefined),
      review_text: review.value || undefined,
      finished_at: finishedAtIso,
    });
    emit('added');
    emit('close');
  } catch (error) {
    console.error('Failed to add title:', error);
  } finally {
    isSubmitting.value = false;
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

      <div class="p-6 space-y-8 overflow-y-auto">
        
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
            class="w-full h-32 bg-zinc-800 rounded-lg p-3 text-white resize-none outline-none focus:ring-2 focus:ring-primary-500 placeholder-zinc-600"
            placeholder="Напишите ваше мнение..."
            maxlength="5000"
          ></textarea>
          <div class="flex justify-between pl-2">
            <span class="text-xs text-zinc-500">{{ review.length }} / 5000</span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-zinc-800 flex justify-end gap-3 bg-zinc-900">
        <AppButton variant="ghost" @click="$emit('close')">Отмена</AppButton>
        <AppButton :disabled="isSubmitDisabled" :loading="isSubmitting" @click="handleSubmit">
          Добавить
        </AppButton>
      </div>
    
    </div>
  </div>
</template>
