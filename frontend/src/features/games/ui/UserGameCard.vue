<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { type UserTitleStatus } from '@/entities/title';
import { TitleCategory } from '@/entities/title';

interface Title {
  id: number;
  name: string;
  category: TitleCategory;
  cover_image: string | null;
  release_year: number | null;
  genres: string[] | null;
}

interface UserTitle {
  id: number;
  user_id: number;
  title_id: number;
  status: UserTitleStatus;
  score: number | null;
  review_text: string | null;
  is_spoiler?: boolean;
  title: Title;
  finished_at?: string | null;
}

const props = withDefaults(defineProps<{
  userTitle: UserTitle;
  editable?: boolean;
}>(), {
  editable: false
});

defineEmits<{
  (e: 'edit', userTitle: UserTitle): void;
}>();

const score = computed(() => {
  if (props.userTitle.score === null) return null;
  return props.userTitle.score === 10 ? '10' : props.userTitle.score.toFixed(1);
});

const statusLabel = computed(() => {
    // Basic mapping, can be moved to shared helper if needed
    const s = props.userTitle.status;
    const cat = props.userTitle.title.category;
    if (s === 'completed') return cat === 'game' ? 'Прошел' : 'Посмотрел';
    if (s === 'playing') return cat === 'game' ? 'Играю' : 'Смотрю';
    if (s === 'watching') return 'Смотрю';
    if (s === 'dropped') return 'Дропнул';
    if (s === 'planned') return 'В планах';
    if (s === 'on_hold') return 'На паузе';
    return s;
});

const statusColorClass = computed(() => {
    const s = props.userTitle.status;
    if (s === 'completed') return 'bg-emerald-100 text-emerald-700';
    if (s === 'playing' || s === 'watching') return 'bg-blue-100 text-blue-700';
    if (s === 'on_hold') return 'bg-amber-100 text-amber-700';
    if (s === 'planned') return 'bg-slate-100 text-slate-700';
    if (s === 'dropped') return 'bg-red-100 text-red-700';
    return 'bg-gray-100 text-gray-700';
});

const isRevealed = ref(false);
const isExpanded = ref(false);
const shouldShowReadMore = computed(() => {
    return (props.userTitle.review_text?.length || 0) > 300;
});

interface ParsedSegment {
    id: number;
    text: string;
    isSpoiler: boolean;
    isRevealed: boolean;
}

const parsedReview = ref<ParsedSegment[]>([]);

// Re-parse when review text changes
watch(() => props.userTitle.review_text, (newText: string | null) => {
    if (!newText) {
        parsedReview.value = [];
        return;
    }
    
    const parts = newText.split(/(<[^<>]+>)/g);
    parsedReview.value = parts.map((part: string, index: number) => {
        if (part.startsWith('<') && part.endsWith('>') && part.length > 2) {
            return {
                id: index,
                text: part.slice(1, -1),
                isSpoiler: true,
                isRevealed: false
            };
        }
        return {
            id: index,
            text: part,
            isSpoiler: false,
            isRevealed: false
        };
    }).filter((part: ParsedSegment) => part.text.length > 0);
}, { immediate: true });

const toggleSpoiler = (id: number) => {
    const segment = parsedReview.value.find(s => s.id === id);
    if (segment) {
        segment.isRevealed = !segment.isRevealed;
    }
};

const router = useRouter();

const goToReview = () => {
  router.push(`/review/${props.userTitle.id}`);
};
</script>

<template>
  <div 
    class="game-card flex gap-5 p-5 bg-[var(--color-bg-primary)] border border-[var(--color-border-primary)] rounded-xl shadow-sm hover:shadow-md transition-all cursor-pointer"
    @click="goToReview"
  >
    <!-- Poster -->
    <div class="w-32 h-44 bg-[var(--color-bg-tertiary)] rounded-lg flex-shrink-0 overflow-hidden shadow-sm relative group">
      <img 
        v-if="userTitle.title.cover_image" 
        :src="userTitle.title.cover_image" 
        :alt="userTitle.title.name"
        class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-[var(--color-text-tertiary)] text-xs text-center p-2">
        No Image
      </div>
    </div>
    
    <!-- Content -->
    <div class="flex flex-col flex-grow py-1 justify-center">
      
      <!-- Top Row: Badge & Status -->
      <div class="flex items-center gap-3 mb-2">
        <span 
          v-if="score"
          class="px-2.5 py-1 bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] rounded-md font-bold text-sm border border-[var(--color-border-primary)]"
        >
          ★ {{ score }}
        </span>
        
        <span 
          class="text-xs px-2.5 py-1 rounded-full font-medium"
          :class="statusColorClass"
        >
          {{ statusLabel }}
        </span>
        
        <button 
          v-if="editable"
          class="ml-auto p-1.5 text-[var(--color-text-tertiary)] hover:text-[var(--color-primary-500)] hover:bg-[var(--color-bg-tertiary)] rounded-full transition-colors"
          @click.stop="$emit('edit', userTitle)"
          title="Редактировать"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
      </div>

      <!-- Title -->
      <h3 class="font-extrabold text-2xl text-[var(--color-text-primary)] line-clamp-2 leading-tight mb-2">
        {{ userTitle.title.name }}
      </h3>
      
      <!-- Meta -->
      <div class="text-sm text-[var(--color-text-secondary)] mb-3 font-medium">
        <span v-if="userTitle.title.release_year">{{ userTitle.title.release_year }}</span>
        <span v-if="userTitle.title.release_year && userTitle.title.genres?.length" class="mx-1.5">•</span>
        <span v-if="userTitle.title.genres?.length" class="opacity-80">
            {{ userTitle.title.genres.slice(0, 3).join(', ') }}
        </span>
      </div>

      <!-- Review -->
      <!-- Review -->
      <div v-if="userTitle.review_text" class="text-sm text-[var(--color-text-secondary)] max-w-2xl">
        <div 
          class="leading-relaxed opacity-90 transition-all duration-300 break-words whitespace-pre-wrap"
          :class="{ 'line-clamp-3': !isExpanded && !isRevealed }" 
        >
          <span 
            v-for="segment in parsedReview" 
            :key="segment.id"
            :class="[
              segment.isSpoiler ? 'cursor-pointer transition-all duration-200 py-0.5 px-1 rounded mx-0.5 select-none' : '',
              segment.isSpoiler && !segment.isRevealed ? 'spoiler-hidden' : '',
              segment.isSpoiler && segment.isRevealed ? 'spoiler-revealed' : ''
            ]"
            @click.stop="segment.isSpoiler && toggleSpoiler(segment.id)"
            :title="segment.isSpoiler && !segment.isRevealed ? 'Нажмите, чтобы показать спойлер' : ''"
          >{{ segment.text }}</span>
        </div>
        
        <button 
          v-if="shouldShowReadMore" 
          @click.stop="isExpanded = !isExpanded" 
          class="text-primary-500 hover:text-primary-600 hover:underline text-xs mt-1 font-medium cursor-pointer"
        >
          {{ isExpanded ? 'Свернуть' : 'Читать далее' }}
        </button>
      </div>
      <!-- <p v-else class="text-sm text-[var(--color-text-tertiary)] italic">
        Нет отзыва
      </p> -->

    </div>
  </div>
</template>

<style scoped>
.spoiler-hidden {
  background: #3f3f46;
  color: transparent;
  filter: blur(4px);
  border-radius: 4px;
  transition: all 0.2s;
}
.spoiler-hidden:hover {
  background: #52525b;
}
.spoiler-revealed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-text-primary);
  transition: all 0.2s;
}

.game-card:hover {
  border-color: var(--color-primary-500);
}
</style>
